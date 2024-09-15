from __future__ import annotations

import calendar
import datetime
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    import discord

    from lumina.types import Interaction

T = TypeVar("T")


def split_list_to_chunks(lst: list[T], chunk_size: int) -> list[list[T]]:
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def absolute_send(
    i: Interaction,
    *,
    embed: discord.Embed | None = None,
    embeds: Sequence[discord.Embed] | None = None,
    view: discord.ui.View | None = None,
    content: str | None = None,
    ephemeral: bool = False,
) -> None:
    kwargs: dict[str, Any] = {"ephemeral": ephemeral}
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view
    if content is not None:
        kwargs["content"] = content
    if embeds is not None:
        if not embeds:
            msg = "embeds must not be empty"
            raise ValueError(msg)
        kwargs["embeds"] = embeds

    if i.response.is_done():
        await i.followup.send(**kwargs)
    else:
        await i.response.send_message(**kwargs)


async def absolute_edit(
    i: Interaction,
    *,
    embed: discord.Embed | None = None,
    embeds: Sequence[discord.Embed] | None = None,
    view: discord.ui.View | None = None,
    content: str | None = None,
) -> None:
    kwargs: dict[str, Any] = {"embed": embed, "embeds": embeds, "view": view, "content": content}

    if i.response.is_done():
        await i.edit_original_response(**kwargs)
    else:
        await i.response.edit_message(**kwargs)


def astimezone(dt: datetime.datetime, tz: int) -> datetime.datetime:
    return dt.astimezone(datetime.timezone(datetime.timedelta(hours=tz)))


def get_now(timezone: int) -> datetime.datetime:
    return astimezone(datetime.datetime.now(), timezone)


def shorten_text(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def next_leap_year() -> int:
    year = get_now(0).year
    while not calendar.isleap(year):
        year += 1
    return year
