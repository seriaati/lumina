from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import discord
from dateutil import parser
from discord import app_commands
from discord.ext import commands

from lumina.components import Modal, Paginator, TextInput
from lumina.exceptions import NoRemindersError, NotFutureTimeError, ReminderNotFoundError
from lumina.l10n import LocaleStr, translator
from lumina.models import LuminaUser, Reminder, get_locale, get_timezone
from lumina.utils import get_now, shorten_text, split_list_to_chunks

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.embeds import DefaultEmbed
    from lumina.types import Interaction


class ReminderModal(Modal):
    time = TextInput(
        label=LocaleStr("reminder_modal_time_label"), placeholder=LocaleStr("reminder_modal_time_placeholder")
    )


class ReminderCog(commands.GroupCog, name=app_commands.locale_str("reminder", key="reminder_group_name")):  # type: ignore
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

        self.set_reminder_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Set reminder", key="set_reminder_ctx_menu_name"), callback=self.set_reminder
        )

    @staticmethod
    def natural_language_to_dt(time: str, timezone: int) -> datetime.datetime:
        dt = parser.parse(time)
        dt = dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=timezone)))
        if dt < get_now(timezone):
            raise NotFutureTimeError
        return dt

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.set_reminder_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.set_reminder_ctx_menu.name, type=self.set_reminder_ctx_menu.type)

    async def set_reminder(self, i: Interaction, message: discord.Message) -> Any:
        locale = await get_locale(i)

        modal = ReminderModal(title=LocaleStr("set_reminder_ctx_menu_name"))
        modal.translate(locale)

        await i.response.send_modal(modal)
        await modal.wait()
        if modal.incomplete:
            return

        timezone = await get_timezone(i.user.id)
        dt = self.natural_language_to_dt(modal.time.value, timezone)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        reminder = await Reminder.create(
            text=message.content or translator.translate(LocaleStr("no_content"), locale=locale),
            datetime=dt,
            user=user,
            message_url=message.jump_url,
        )
        await self.bot.scheduler.schedule_reminder()

        await i.followup.send(embed=reminder.get_created_embed(locale), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("set", key="birthday_set_command_name"),
        description=app_commands.locale_str("Set a reminder", key="reminder_set_command_description"),
    )
    @app_commands.rename(
        when=app_commands.locale_str("when", key="when_parameter_name"),
        text=app_commands.locale_str("text", key="text_parameter_name"),
    )
    @app_commands.describe(
        when=app_commands.locale_str(
            "When to remind you (e.g. in 1 hour, December 21st)", key="reminder_set_when_param_desc"
        ),
        text=app_commands.locale_str("What to remind you of", key="reminder_set_text_param_desc"),
    )
    async def reminder_set(self, i: Interaction, when: str, text: str) -> None:
        await i.response.defer(ephemeral=True)

        timezone = await get_timezone(i.user.id)
        dt = self.natural_language_to_dt(when, timezone)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        reminder = await Reminder.create(text=text, datetime=dt, user=user)
        await self.bot.scheduler.schedule_reminder()

        await i.followup.send(embed=reminder.get_created_embed(await get_locale(i)), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("remove", key="birthday_remove_command_name"),
        description=app_commands.locale_str("Remove a reminder", key="reminder_remove_command_description"),
    )
    @app_commands.rename(reminder_id=app_commands.locale_str("reminder", key="reminder_parameter_name"))
    @app_commands.describe(
        reminder_id=app_commands.locale_str("The reminder to remove", key="reminder_remove_param_desc")
    )
    async def reminder_remove(self, i: Interaction, reminder_id: int) -> None:
        reminder = await Reminder.get_or_none(id=reminder_id)
        if reminder is None:
            raise ReminderNotFoundError

        await reminder.delete()
        await self.bot.scheduler.schedule_reminder()

        await i.response.send_message(embed=reminder.get_removed_embed(await get_locale(i)), ephemeral=True)

    @reminder_remove.autocomplete("reminder_id")
    async def reminder_id_autocomplete(self, i: Interaction, current: str) -> list[app_commands.Choice[int]]:
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        reminders = await Reminder.filter(user=user).all()

        if not reminders:
            return [
                app_commands.Choice(
                    name=translator.translate(LocaleStr("no_reminders_title"), locale=await get_locale(i)), value=-1
                )
            ]

        return [
            app_commands.Choice(name=shorten_text(reminder.text, 100), value=reminder.id)
            for reminder in reminders
            if current.lower() in reminder.text.lower()
        ][:25]

    @app_commands.command(
        name=app_commands.locale_str("list", key="birthday_list_command_name"),
        description=app_commands.locale_str("List all reminders you have set", key="reminder_list_command_description"),
    )
    async def reminder_list(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        reminders = await Reminder.filter(user=user).all().order_by("datetime")
        if not reminders:
            raise NoRemindersError

        split_reminders = split_list_to_chunks(reminders, 10)
        locale = await get_locale(i)
        embeds: list[DefaultEmbed] = []

        for index, bdays in enumerate(split_reminders):
            embeds.append(Reminder.get_list_embed(locale, reminders=bdays, start=1 + index * 10))

        view = Paginator(embeds, locale=locale)
        await view.start(i)


async def setup(bot: Lumina) -> None:
    await bot.add_cog(ReminderCog(bot))
