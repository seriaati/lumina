from __future__ import annotations

from typing import TYPE_CHECKING, Any

from discord import Message, TextStyle, app_commands
from discord.ext import commands

from lumina.components import Modal, Paginator, TextInput
from lumina.exceptions import NoNotesError, NoteNotFoundError
from lumina.l10n import LocaleStr
from lumina.models import Notes, get_locale
from lumina.utils import shorten_text, split_list_to_chunks

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.embeds import DefaultEmbed
    from lumina.types import Interaction


class NotesModal(Modal):
    note_title = TextInput(
        label=LocaleStr("notes_modal_title_label"), default=LocaleStr("notes_modal_untitled")
    )
    note_content = TextInput(label=LocaleStr("notes_modal_content_label"), style=TextStyle.long)


class NotesCog(commands.GroupCog, name=app_commands.locale_str("notes", key="notes_group_name")):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

        self.save_to_notes_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Save to notes", key="save_to_notes_ctx_menu_name"),
            callback=self.save_to_notes_ctx,
        )

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.save_to_notes_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.save_to_notes_ctx_menu.name, type=self.save_to_notes_ctx_menu.type
        )

    async def save_to_notes_ctx(self, i: Interaction, message: Message) -> Any:
        return await self.save_to_notes(i, message=message)

    async def save_to_notes(self, i: Interaction, *, message: Message | None = None) -> Any:
        locale = await get_locale(i)

        modal = NotesModal(title=LocaleStr("notes_modal_title"))
        if message is not None:
            modal.note_content.default = message.content
        modal.translate(i.client.translator, locale)

        await i.response.send_modal(modal)
        await modal.wait()
        if modal.incomplete:
            return

        notes = await Notes.create(
            title=modal.note_title.value
            or i.client.translator.translate(LocaleStr("notes_modal_untitled"), locale=locale),
            content=modal.note_content.value,
            user_id=i.user.id,
        )
        await i.followup.send(
            embed=notes.get_created_embed(i.client.translator, locale), ephemeral=True
        )

    @app_commands.command(
        name=app_commands.locale_str("write", key="notes_write_command_name"),
        description=app_commands.locale_str(
            "Write a new note", key="notes_write_command_description"
        ),
    )
    async def notes_write(self, i: Interaction) -> None:
        return await self.save_to_notes(i)

    @app_commands.command(
        name=app_commands.locale_str("remove", key="birthday_remove_command_name"),
        description=app_commands.locale_str(
            "Remove a note", key="notes_remove_command_description"
        ),
    )
    @app_commands.rename(note_id=app_commands.locale_str("note", key="note_parameter_name"))
    async def notes_remove(self, i: Interaction, note_id: int) -> None:
        await i.response.defer(ephemeral=True)

        notes = await Notes.get_or_none(id=note_id)
        if notes is None:
            raise NoteNotFoundError

        await notes.delete()
        await i.followup.send(
            embed=notes.get_removed_embed(i.client.translator, await get_locale(i)), ephemeral=True
        )

    @app_commands.command(
        name=app_commands.locale_str("list", key="birthday_list_command_name"),
        description=app_commands.locale_str("List all notes", key="notes_list_command_description"),
    )
    async def notes_list(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)

        notes = await Notes.filter(user_id=i.user.id).all()
        if not notes:
            raise NoNotesError

        chunked_notes = split_list_to_chunks(notes, 10)
        locale = await get_locale(i)
        embeds: list[DefaultEmbed] = []

        for index, notes_ in enumerate(chunked_notes):
            embeds.append(
                Notes.get_list_embed(
                    i.client.translator, locale, notes=notes_, start=1 + index * 10
                )
            )

        view = Paginator(embeds, translator=i.client.translator, locale=locale)
        await view.start(i)

    @app_commands.command(
        name=app_commands.locale_str("read", key="notes_read_command_name"),
        description=app_commands.locale_str("Read a note", key="notes_read_command_description"),
    )
    @app_commands.rename(note_id=app_commands.locale_str("note", key="note_parameter_name"))
    async def notes_read(self, i: Interaction, note_id: int) -> None:
        await i.response.defer(ephemeral=True)

        notes = await Notes.get_or_none(id=note_id)
        if notes is None:
            raise NoteNotFoundError

        await i.followup.send(content=f"# {notes.title}\n\n{notes.content}", ephemeral=True)

    @notes_remove.autocomplete("note_id")
    @notes_read.autocomplete("note_id")
    async def note_id_autocomplete(
        self, i: Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        notes = await Notes.filter(user_id=i.user.id).all()

        if not notes:
            return [
                app_commands.Choice(
                    name=i.client.translator.translate(
                        LocaleStr("no_notes_title"), locale=await get_locale(i)
                    ),
                    value=-1,
                )
            ]

        return [
            app_commands.Choice(name=shorten_text(note.title, 100), value=note.id)
            for note in notes
            if current.lower() in note.title.lower()
        ][:25]


async def setup(bot: Lumina) -> None:
    await bot.add_cog(NotesCog(bot))
