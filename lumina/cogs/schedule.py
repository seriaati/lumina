from __future__ import annotations

import calendar
from typing import TYPE_CHECKING

from discord.ext import commands, tasks
from loguru import logger

from lumina.constants import DEFAULT_LOCALE
from lumina.models import Birthday, LuminaUser
from lumina.utils import get_now

if TYPE_CHECKING:
    from lumina.bot import Lumina


class ScheduleCog(commands.Cog):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.notify_birthdays.start()

    async def cog_unload(self) -> None:
        self.notify_birthdays.cancel()

    @tasks.loop(hours=1)
    async def notify_birthdays(self) -> None:
        timezones: list[int] = (
            await LuminaUser.filter().distinct().values_list("timezone", flat=True)  # pyright: ignore[reportAssignmentType]
        )

        for timezone in timezones:
            now = get_now(timezone)
            is_leap_year = calendar.isleap(now.year)

            birthdays = await Birthday.filter(
                month=now.month, day=now.day, user__timezone=timezone, last_notify_year__lt=now.year
            ).all()

            for birthday in birthdays:
                if (
                    (birthday.month, birthday.day) == (2, 29)
                    and not is_leap_year
                    and (birthday.leap_year_notify_month, birthday.leap_year_notify_day) != (now.month, now.day)
                ):
                    continue

                logger.info(f"Sending birthday reminder to {birthday.user_id}")
                await birthday.fetch_related("user")
                embed = birthday.get_embed(birthday.user.locale or DEFAULT_LOCALE)
                success = await self.bot.dm_user(birthday.user_id, embed=embed)
                if success:
                    birthday.last_notify_year = now.year
                    await birthday.save(update_fields=("last_notify_year",))

    @notify_birthdays.before_loop
    async def before_run_reminders(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: Lumina) -> None:
    await bot.add_cog(ScheduleCog(bot))
