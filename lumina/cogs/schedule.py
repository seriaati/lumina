from __future__ import annotations

import calendar
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks
from loguru import logger

from lumina.models import LuminaUser
from lumina.utils import get_now

if TYPE_CHECKING:
    from lumina.bot import Lumina


class ReminderCog(commands.Cog):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.send_notifications.start()

    async def cog_unload(self) -> None:
        self.send_notifications.cancel()

    @tasks.loop(minutes=1)
    async def send_notifications(self) -> None:
        default_locale = discord.Locale.american_english
        users = await LuminaUser.all().prefetch_related("birthdays", "reminders")

        for user in users:
            now = get_now(user.timezone)
            is_leap_year = calendar.isleap(now.year)

            for bday in user.birthdays:
                if (bday.month == now.month and bday.day == now.day) or (  # noqa: PLR0916
                    (
                        (bday.month, bday.day) == (2, 29)
                        and not is_leap_year
                        and (bday.leap_year_notify_month, bday.leap_year_notify_day)
                        == (now.month, now.day)
                    )
                    and bday.last_notify_year != now.year
                ):
                    embed = bday.get_embed(self.bot.translator, user.locale or default_locale)
                    logger.info(f"Sending birthday reminder to {bday.bday_user_id}")
                    success = await self.bot.dm_user(user.id, embed=embed)
                    if success:
                        bday.last_notify_year = now.year
                        await bday.save(update_fields=("last_notify_year",))

            for reminder in user.reminders:
                if reminder.get_adjusted_datetime(user) <= now:
                    embed = reminder.get_embed(self.bot.translator, user.locale or default_locale)
                    success = await self.bot.dm_user(user.id, embed=embed)
                    if success:
                        await reminder.delete()

    @send_notifications.before_loop
    async def before_run_reminders(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: Lumina) -> None:
    await bot.add_cog(ReminderCog(bot))
