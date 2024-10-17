from __future__ import annotations

from typing import TYPE_CHECKING, Self

import discord

from lumina.l10n import LocaleStr

if TYPE_CHECKING:
    from lumina.l10n import Translator


class LuminaEmbed(discord.Embed):
    def __init__(
        self,
        translator: Translator,
        locale: discord.Locale,
        *,
        title: LocaleStr | str | None = None,
        description: LocaleStr | str | None = None,
        url: str | None = None,
        color: discord.Color | int,
    ) -> None:
        self.translator = translator
        self.locale = locale

        if isinstance(title, LocaleStr):
            title = translator.translate(title, locale=locale)
        if isinstance(description, LocaleStr):
            description = translator.translate(description, locale=locale)

        super().__init__(title=title, description=description, url=url, color=color)

    def set_footer(self, *, text: LocaleStr | str | None, icon_url: str | None = None) -> Self:
        if isinstance(text, LocaleStr):
            text = self.translator.translate(text, locale=self.locale)
        return super().set_footer(text=text, icon_url=icon_url)


class DefaultEmbed(LuminaEmbed):
    def __init__(
        self,
        translator: Translator,
        locale: discord.Locale,
        *,
        title: LocaleStr | str | None = None,
        description: LocaleStr | str | None = None,
        url: str | None = None,
    ) -> None:
        self.translator = translator
        self.locale = locale

        super().__init__(translator, locale, title=title, description=description, url=url, color=16757760)


class ErrorEmbed(LuminaEmbed):
    def __init__(
        self,
        translator: Translator,
        locale: discord.Locale,
        *,
        title: LocaleStr | str | None = None,
        description: LocaleStr | str | None = None,
        url: str | None = None,
    ) -> None:
        self.translator = translator
        self.locale = locale

        super().__init__(translator, locale, title=title, description=description, url=url, color=15169131)
