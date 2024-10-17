from __future__ import annotations

from lumina.l10n import LocaleStr


class LuminaError(Exception):
    def __init__(self, title: LocaleStr, description: LocaleStr | None = None) -> None:
        self.title = title
        self.description = description


class InvalidInputError(LuminaError):
    def __init__(self, value: str) -> None:
        super().__init__(
            LocaleStr("invalid_input_title"), LocaleStr("invalid_input_description", params={"value": value})
        )


class DidNotSetBirthdayError(LuminaError):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            LocaleStr("did_not_set_birthday_title"),
            LocaleStr("did_not_set_birthday_description", params={"user_id": user_id}),
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


class NoNotesError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("no_notes_title"))


class NoteNotFoundError(LuminaError):
    def __init__(self) -> None:
        super().__init__(LocaleStr("note_not_found_title"))
