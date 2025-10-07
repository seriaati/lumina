from __future__ import annotations

from typing import Any

import aiofiles
import anyio
import discord
import yaml


class LocaleStr:
    def __init__(self, key: str, *, params: dict[str, Any] | None = None) -> None:
        self.key = key
        self.params = params or {}


class Translator:
    def __init__(self) -> None:
        self.translations: dict[str, dict[str, str]] = {}

    async def load(self) -> None:
        """Load all translations from the l10n directory."""
        async for file_path in anyio.Path("./l10n").rglob("*.yaml"):
            async with aiofiles.open(file_path, encoding="utf-8") as file:
                data: dict[str, str] = yaml.safe_load(await file.read())

            language = file_path.stem
            self.translations[language] = data

        if discord.Locale.american_english.value not in self.translations:
            msg = "en-US.yaml not found"
            raise FileNotFoundError(msg)

    def translate(self, string: LocaleStr, *, locale: discord.Locale) -> str:
        """Translate a string to the given locale.

        If the key is not found in the source locale, raise a KeyError.
        If the key is not found in the given locale, return the source string.

        Args:
            string: The string to translate.
            locale: The locale to translate to.

        Returns:
            The translated string.
        """
        try:
            source_str = self.translations[discord.Locale.american_english.value][string.key]
        except KeyError as e:
            msg = f"Key {string.key!r} not found in en-US.yaml"
            raise KeyError(msg) from e

        try:
            translation = self.translations[locale.value][string.key]
        except KeyError:
            return source_str.format_map(string.params)

        return translation.format_map(string.params)


translator = Translator()


class AppCommandTranslator(discord.app_commands.Translator):
    async def translate(
        self,
        string: discord.app_commands.locale_str,
        locale: discord.Locale,
        _: discord.app_commands.TranslationContextTypes,
    ) -> str:
        if (key := string.extras.get("key")) is None:
            return string.message
        return translator.translate(LocaleStr(key=key), locale=locale)
