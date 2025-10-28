from __future__ import annotations

import calendar
import contextlib
from datetime import timedelta
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks
from loguru import logger

from lumina.constants import DEFAULT_LOCALE
from lumina.models import Birthday, LuminaUser
from lumina.utils import get_now

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.types import UserOrMember


class ScheduleCog(commands.Cog):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.notify_birthdays.start()

    async def cog_unload(self) -> None:
        self.notify_birthdays.cancel()

    async def _get_bday_user(self, birthday: Birthday) -> UserOrMember | None:
        bday_user: UserOrMember | None = None
        if birthday.bday_user_id != 0:
            with contextlib.suppress(discord.NotFound):
                bday_user = self.bot.get_user(birthday.bday_user_id) or await self.bot.fetch_user(birthday.bday_user_id)
        return bday_user

    async def _send_regular_notification(self, birthday: Birthday) -> None:
        """Send a regular birthday notification on the day of the birthday."""
        logger.info(f"Sending birthday reminder to {birthday.user_id}")
        await birthday.fetch_related("user")

        bday_user = await self._get_bday_user(birthday)

        embed = birthday.get_embed(birthday.user.locale or DEFAULT_LOCALE, user=bday_user)
        success = await self.bot.dm_user(birthday.user_id, embed=embed)
        if success:
            user = await LuminaUser.get(id=birthday.user_id)
            birthday.last_notify_year = get_now(user.timezone).year
            await birthday.save(update_fields=("last_notify_year",))

    async def _send_early_notification(self, birthday: Birthday, days_before: int) -> None:
        """Send an early birthday notification X days before the birthday."""
        logger.info(f"Sending early birthday reminder to {birthday.user_id} ({days_before} days before)")
        await birthday.fetch_related("user")

        bday_user = await self._get_bday_user(birthday)

        embed = birthday.get_early_notification_embed(
            birthday.user.locale or DEFAULT_LOCALE, user=bday_user, days_before=days_before
        )
        success = await self.bot.dm_user(birthday.user_id, embed=embed)
        if success:
            user = await LuminaUser.get(id=birthday.user_id)
            birthday.last_early_notify_year = get_now(user.timezone).year
            await birthday.save(update_fields=("last_early_notify_year",))

    @tasks.loop(hours=1)
    async def notify_birthdays(self) -> None:
        timezones: list[int] = (
            await LuminaUser.filter().distinct().values_list("timezone", flat=True)  # pyright: ignore[reportAssignmentType]
        )

        for timezone in timezones:
            await self._process_regular_birthdays(timezone)
            await self._process_early_notifications(timezone)

    async def _process_regular_birthdays(self, timezone: int) -> None:
        """Process and send regular birthday notifications for today."""
        now = get_now(timezone)
        is_leap_year = calendar.isleap(now.year)

        birthdays = await Birthday.filter(
            month=now.month, day=now.day, user__timezone=timezone, last_notify_year__lt=now.year
        ).all()

        for birthday in birthdays:
            should_notify = self._check_leap_year_notification(birthday, now.month, now.day, is_leap_year=is_leap_year)
            if should_notify:
                await self._send_regular_notification(birthday)

    async def _process_early_notifications(self, timezone: int) -> None:
        """Process and send early birthday notifications (X days before birthday)."""
        now = get_now(timezone)

        birthdays = await Birthday.filter(
            user__timezone=timezone, notify_days_before__isnull=False, last_early_notify_year__lt=now.year
        ).all()

        for birthday in birthdays:
            if birthday.notify_days_before is None:
                continue

            target_date = self._calculate_target_birthday(birthday, now)
            if target_date is None:
                continue

            early_notify_date = target_date - timedelta(days=birthday.notify_days_before)

            if early_notify_date.date() == now.date():
                await self._send_early_notification(birthday, birthday.notify_days_before)

    def _check_leap_year_notification(
        self, birthday: Birthday, now_month: int, now_day: int, *, is_leap_year: bool
    ) -> bool:
        """Check if a birthday notification should be sent, considering leap year edge cases."""
        if (birthday.month, birthday.day) != (2, 29):
            return True
        if is_leap_year:
            return True
        return (birthday.leap_year_notify_month, birthday.leap_year_notify_day) == (now_month, now_day)

    def _calculate_target_birthday(self, birthday: Birthday, now):  # noqa: ANN001, ANN202
        """Calculate the target birthday date for the current or next year. Returns datetime or None."""
        try:
            target_date = now.replace(month=birthday.month, day=birthday.day)
        except ValueError:
            return None

        if target_date < now:
            try:
                return target_date.replace(year=now.year + 1)
            except ValueError:
                return None

        return target_date

    @notify_birthdays.before_loop
    async def before_run_reminders(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: Lumina) -> None:
    await bot.add_cog(ScheduleCog(bot))
