from __future__ import annotations

from typing import TYPE_CHECKING

from lumina.embeds import ErrorEmbed
from lumina.exceptions import LuminaError
from lumina.l10n import LocaleStr

if TYPE_CHECKING:
    import discord


def create_error_embed(error: Exception, *, locale: discord.Locale) -> tuple[ErrorEmbed, bool]:
    """Create an error embed from an exception.

    Args:
        error: The exception to create an embed from.
        translator: The translator to use.
        locale: The locale to translate to.

    Returns:
        A tuple containing the error embed and a boolean indicating if the error was recognized.
    """
    if isinstance(error, LuminaError):
        return ErrorEmbed(locale, title=error.title, description=error.description), True

    return ErrorEmbed(locale, title=LocaleStr("unknown_error"), description=f"{type(error).__name__}: {error}"), False
