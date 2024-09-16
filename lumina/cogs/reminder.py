from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import discord
import parsedatetime
from discord import app_commands
from discord.ext import commands

from lumina.components import Modal, Paginator, TextInput
from lumina.exceptions import NoRemindersError, ReminderNotFoundError
from lumina.l10n import LocaleStr
from lumina.models import LuminaUser, Reminder, get_locale
from lumina.utils import get_now, shorten_text, split_list_to_chunks

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.embeds import DefaultEmbed
    from lumina.types import Interaction


class ReminderModal(Modal):
    time = TextInput(
        label=LocaleStr("reminder_modal_time_label"),
        placeholder=LocaleStr("reminder_modal_time_placeholder"),
    )


class ReminderCog(
    commands.GroupCog, name=app_commands.locale_str("reminder", key="reminder_group_name")
):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

        self.set_reminder_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Set reminder", key="set_reminder_ctx_menu_name"),
            callback=self.set_reminder,
        )

    @staticmethod
    def natural_language_to_datetime(time: str) -> datetime.datetime:
        cal = parsedatetime.Calendar()
        time_struct, _ = cal.parse(time, get_now(0))
        return datetime.datetime(*time_struct[:6]).replace(tzinfo=datetime.UTC)

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.set_reminder_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.set_reminder_ctx_menu.name, type=self.set_reminder_ctx_menu.type
        )

    async def set_reminder(self, i: Interaction, message: discord.Message) -> Any:
        locale = await get_locale(i)

        modal = ReminderModal(title=LocaleStr("set_reminder_ctx_menu_name"))
        modal.translate(i.client.translator, locale)

        await i.response.send_modal(modal)
        await modal.wait()
        if modal.incomplete:
            return

        dt = self.natural_language_to_datetime(modal.time.value)
        timezone = (await LuminaUser.get_or_create(id=i.user.id))[0].timezone

        reminder = await Reminder.create(
            text=message.content
            or i.client.translator.translate(LocaleStr("no_content"), locale=locale),
            datetime=dt,
            user_id=i.user.id,
            message_url=message.jump_url,
        )
        await i.followup.send(
            embed=reminder.get_created_embed(i.client.translator, locale, timezone), ephemeral=True
        )

    @app_commands.command(
        name=app_commands.locale_str("set", key="birthday_set_command_name"),
        description=app_commands.locale_str(
            "Set a reminder", key="reminder_set_command_description"
        ),
    )
    @app_commands.rename(
        when=app_commands.locale_str("when", key="when_parameter_name"),
        text=app_commands.locale_str("text", key="text_parameter_name"),
    )
    @app_commands.describe(
        text=app_commands.locale_str("text", key="text_param_description_reminder")
    )
    async def reminder_set(self, i: Interaction, when: str, text: str) -> None:
        await i.response.defer(ephemeral=True)

        dt = self.natural_language_to_datetime(when)
        timezone = (await LuminaUser.get_or_create(id=i.user.id))[0].timezone

        reminder = await Reminder.create(text=text, datetime=dt, user_id=i.user.id)
        await i.followup.send(
            embed=reminder.get_created_embed(i.client.translator, await get_locale(i), timezone),
            ephemeral=True,
        )

    @app_commands.command(
        name=app_commands.locale_str("remove", key="birthday_remove_command_name"),
        description=app_commands.locale_str(
            "Remove a reminder", key="reminder_remove_command_description"
        ),
    )
    @app_commands.rename(
        reminder_id=app_commands.locale_str("reminder", key="reminder_parameter_name")
    )
    async def birthday_remove(self, i: Interaction, reminder_id: int) -> None:
        reminder = await Reminder.get_or_none(id=reminder_id)
        if reminder is None:
            raise ReminderNotFoundError

        await reminder.delete()
        await i.response.send_message(
            embed=reminder.get_removed_embed(i.client.translator, await get_locale(i)),
            ephemeral=True,
        )

    @birthday_remove.autocomplete("reminder_id")
    async def reminder_id_autocomplete(
        self, i: Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        reminders = await Reminder.filter(user_id=i.user.id).all()

        if not reminders:
            return [
                app_commands.Choice(
                    name=i.client.translator.translate(
                        LocaleStr("no_reminders_title"), locale=await get_locale(i)
                    ),
                    value=-1,
                )
            ]

        return [
            app_commands.Choice(name=shorten_text(reminder.text, 100), value=reminder.id)
            for reminder in reminders
            if current.lower() in reminder.text.lower()
        ][:25]

    @app_commands.command(
        name=app_commands.locale_str("list", key="birthday_list_command_name"),
        description=app_commands.locale_str(
            "List all reminders you have set", key="reminder_list_command_description"
        ),
    )
    async def birthday_list(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)

        reminders = await Reminder.filter(user_id=i.user.id).all()
        if not reminders:
            raise NoRemindersError

        split_reminders = split_list_to_chunks(reminders, 10)
        timezone = (await LuminaUser.get_or_create(id=i.user.id))[0].timezone
        locale = await get_locale(i)
        embeds: list[DefaultEmbed] = []

        for index, bdays in enumerate(split_reminders):
            embeds.append(
                Reminder.get_list_embed(
                    i.client.translator,
                    locale,
                    reminders=bdays,
                    timezone=timezone,
                    start=1 + index * 10,
                )
            )

        view = Paginator(embeds, translator=i.client.translator, locale=locale)
        await view.start(i)


async def setup(bot: Lumina) -> None:
    await bot.add_cog(ReminderCog(bot))