# pyright: reportAssignmentType=false

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from tortoise import Model, fields

from lumina.embeds import DefaultEmbed
from lumina.l10n import LocaleStr
from lumina.utils import get_now, next_leap_year, shorten_text

if TYPE_CHECKING:
    import datetime

    from lumina.types import Interaction


class BaseModel(Model):
    def __str__(self) -> str:
        attrs_str = ", ".join(
            f"{field}={getattr(self, field)!r}" for field in self._meta.db_fields if hasattr(self, field)
        )
        return f"{self.__class__.__name__}({attrs_str})"

    def __repr__(self) -> str:
        return str(self)

    class Meta:
        abstract = True


class LuminaUser(BaseModel):
    id = fields.BigIntField(pk=True, generated=False)
    timezone = fields.SmallIntField(default=0)
    """The hour offset from UTC."""
    lang: fields.Field[str | None] = fields.CharField(max_length=5, null=True)

    birthdays: fields.ReverseRelation[Birthday]
    reminders: fields.ReverseRelation[Reminder]
    todos: fields.ReverseRelation[TodoTask]
    notes: fields.ReverseRelation[Notes]

    @property
    def locale(self) -> discord.Locale | None:
        return discord.Locale(self.lang) if self.lang else None

    @staticmethod
    def get_settings_saved_embed(locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(locale=locale, title=LocaleStr("settings_saved_embed_title"))


class Birthday(BaseModel):
    id = fields.BigIntField(pk=True, generated=True)

    bday_user_id = fields.BigIntField()
    bday_username: fields.Field[str | None] = fields.CharField(max_length=100, null=True)
    user: fields.ForeignKeyRelation[LuminaUser] = fields.ForeignKeyField("models.LuminaUser", related_name="birthdays")
    user_id: fields.BigIntField

    month = fields.IntField()
    day = fields.IntField()

    leap_year_notify_month: fields.Field[int | None] = fields.IntField(null=True)
    leap_year_notify_day: fields.Field[int | None] = fields.IntField(null=True)
    last_notify_year = fields.IntField(default=0)

    @property
    def user_str(self) -> str:
        user_str = f"<@{self.bday_user_id}>" if self.bday_user_id != 0 else self.bday_username
        return "???" if user_str is None else user_str

    @staticmethod
    def get_correct_dt(*, month: int, day: int, timezone: int) -> datetime.datetime:
        now = get_now(timezone)

        try:
            dt = now.replace(month=month, day=day)
        except ValueError:
            dt = now.replace(year=next_leap_year(), month=month, day=day)

        if dt >= now:
            return dt

        try:
            return dt.replace(year=now.year + 1)
        except ValueError:
            return dt.replace(year=next_leap_year())

    def get_timestamp_md(self, timezone: int) -> str:
        """Get the timestamp in Discord-flavor markdown."""
        return discord.utils.format_dt(Birthday.get_correct_dt(month=self.month, day=self.day, timezone=timezone), "D")

    def get_created_embed(
        self, locale: discord.Locale, *, timezone: int, avatar_url: str | None = None
    ) -> DefaultEmbed:
        dt = Birthday.get_correct_dt(month=self.month, day=self.day, timezone=timezone)
        embed = DefaultEmbed(
            locale=locale,
            title=LocaleStr("birthday_complete_embed_title"),
            description=LocaleStr(
                "birthday_complete_embed_description",
                params={"user": self.user_str, "dt": discord.utils.format_dt(dt, "D")},
            ),
        )
        if avatar_url is not None:
            embed.set_thumbnail(url=avatar_url)

        return embed

    def get_removed_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("birthday_removed_embed_title"),
            description=LocaleStr("birthday_removed_embed_description", params={"user": self.user_str}),
        )

    @staticmethod
    def get_list_embed(locale: discord.Locale, *, birthdays: list[Birthday], timezone: int, start: int) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("birthday_list_embed_title"),
            description="\n".join(
                f"{i}. {bday.user_str}: {bday.get_timestamp_md(timezone)}"
                for i, bday in enumerate(birthdays, start=start)
            ),
        )

    @staticmethod
    def get_leap_year_notify_embed(locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("leap_year_notify_embed_title"),
            description=LocaleStr("leap_year_notify_embed_description"),
        )

    def get_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("birthday_embed_title", params={"user": self.user_str}),
            description=LocaleStr("birthday_embed_description", params={"user": self.user_str}),
        )

    class Meta:
        unique_together = ("bday_user_id", "user", "bday_username")


class Reminder(BaseModel):
    id = fields.IntField(pk=True, generated=True)
    text = fields.TextField()
    datetime = fields.DatetimeField()
    """The time to remind the user in UTC."""
    user: fields.ForeignKeyRelation[LuminaUser] = fields.ForeignKeyField("models.LuminaUser", related_name="reminders")
    user_id: fields.BigIntField
    created_at = fields.DatetimeField(auto_now_add=True)
    message_url: fields.Field[str | None] = fields.TextField(null=True)
    sent = fields.BooleanField(default=False)

    def get_embed(self, locale: discord.Locale) -> DefaultEmbed:
        if self.message_url is not None:
            params = {"message_url": self.message_url, "created_at": discord.utils.format_dt(self.created_at, "R")}
            locale_str_key = "message_reminder_embed_description"
        else:
            params = {"created_at": discord.utils.format_dt(self.created_at, "R")}
            locale_str_key = "reminder_embed_description"

        return DefaultEmbed(
            locale=locale, title=shorten_text(self.text, 100), description=LocaleStr(locale_str_key, params=params)
        )

    def get_created_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("reminder_created_embed_title"),
            description=LocaleStr(
                "reminder_created_embed_description", params={"dt": discord.utils.format_dt(self.datetime, "R")}
            ),
        )

    def get_removed_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(locale=locale, title=LocaleStr("reminder_removed_embed_title"), description=self.text)

    @staticmethod
    def get_list_embed(locale: discord.Locale, *, reminders: list[Reminder], start: int) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("reminder_list_embed_title"),
            description="\n".join(
                f"{i}. {shorten_text(reminder.text, 100)}: {discord.utils.format_dt(reminder.datetime)}"
                for i, reminder in enumerate(reminders, start=start)
            ),
        )


class TodoTask(BaseModel):
    id = fields.IntField(pk=True, generated=True)
    text = fields.TextField()
    user = fields.ForeignKeyField("models.LuminaUser", related_name="todos")
    created_at = fields.DatetimeField(auto_now_add=True)
    done = fields.BooleanField(default=False)

    async def mark_done(self) -> None:
        self.done = True
        await self.save(update_fields=("done",))

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012

    def get_created_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("todo_created_embed_title"),
            description=LocaleStr("todo_created_embed_description", params={"text": self.text}),
        )

    def get_done_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("todo_done_embed_title"),
            description=LocaleStr("todo_done_embed_description", params={"text": self.text}),
        )

    def get_removed_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("todo_removed_embed_title"),
            description=LocaleStr("todo_removed_embed_description", params={"text": self.text}),
        )

    @staticmethod
    def format_todo_text(todo: TodoTask) -> str:
        text = shorten_text(todo.text, 100)
        if todo.done:
            return f"~~{text}~~"
        return text

    @staticmethod
    def get_list_embed(locale: discord.Locale, *, todos: list[TodoTask], start: int) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("todo_list_embed_title"),
            description="\n".join(
                f"{i}. {TodoTask.format_todo_text(todo)}" for i, todo in enumerate(todos, start=start)
            ),
        )


class Notes(BaseModel):
    id = fields.IntField(pk=True, generated=True)
    title = fields.CharField(max_length=100)
    content = fields.TextField()
    user = fields.ForeignKeyField("models.LuminaUser", related_name="notes")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012

    def get_created_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("notes_created_embed_title"),
            description=LocaleStr("notes_created_embed_description", params={"title": self.title}),
        )

    def get_removed_embed(self, locale: discord.Locale) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("notes_removed_embed_title"),
            description=LocaleStr("notes_removed_embed_description", params={"title": self.title}),
        )

    @staticmethod
    def get_list_embed(locale: discord.Locale, *, notes: list[Notes], start: int) -> DefaultEmbed:
        return DefaultEmbed(
            locale=locale,
            title=LocaleStr("notes_list_embed_title"),
            description="\n".join(f"{i}. {shorten_text(note.title, 100)}" for i, note in enumerate(notes, start=start)),
        )


async def get_locale(i: Interaction) -> discord.Locale:
    user, _ = await LuminaUser.get_or_create(id=i.user.id)
    return user.locale or i.locale


async def get_timezone(user_id: int) -> int:
    user, _ = await LuminaUser.get_or_create(id=user_id)
    return user.timezone
