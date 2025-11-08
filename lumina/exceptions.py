from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from lumina.l10n import LocaleStr

if TYPE_CHECKING:
    import datetime


class LuminaError(Exception):
    def __init__(self, title: LocaleStr | str, description: LocaleStr | str | None = None) -> None:
        self.title = title
        self.description = description


class InvalidInputError(LuminaError):
    def __init__(self, value: str) -> None:
        super().__init__(
            LocaleStr("invalid_input_title"), LocaleStr("invalid_input_description", params={"value": value})
        )


class DidNotSetBirthdayError(LuminaError):
    def __init__(self, user: str) -> None:
        super().__init__(
            LocaleStr("did_not_set_birthday_title"),
            LocaleStr("did_not_set_birthday_description", params={"user": user}),
        )


class NoBirthdaysError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("no_birthdays_title"))


class NoRemindersError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("no_reminders_title"))


class ReminderNotFoundError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("reminder_not_found_title"))


class TodoNotFoundError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("todo_not_found_title"))


class NoTasksError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("no_tasks_title"))


class NotFutureTimeError(LuminaError):
    def __init__(self, parsed: datetime.datetime) -> None:
        super().__init__(LocaleStr("not_future_time_error"), discord.utils.format_dt(parsed, "F"))


class InvalidBirthdayInputError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("bday_invalid_input_error_title"), LocaleStr("bday_invalid_input_error_desc"))
