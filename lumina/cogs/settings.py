from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from lumina.exceptions import InvalidInputError
from lumina.l10n import translator
from lumina.models import LuminaUser, get_locale

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.types import Interaction


class SettingsCog(commands.Cog):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

    @app_commands.command(
        name=app_commands.locale_str("language", key="lang_param_name"),
        description=app_commands.locale_str(
            "Set the language of the bot's responses", key="language_command_description"
        ),
    )
    @app_commands.rename(lang=app_commands.locale_str("language", key="lang_param_name"))
    async def set_lang_command(self, i: Interaction, lang: str) -> None:
        if lang not in translator.translations:
            raise InvalidInputError(lang)

        await i.response.defer(ephemeral=True)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        user.lang = lang
        await user.save(update_fields=("lang",))

        embed = user.get_settings_saved_embed(await get_locale(i))
        await i.followup.send(embed=embed, ephemeral=True)

    @set_lang_command.autocomplete("lang")
    async def lang_autocomplete(self, _: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=translations["lang_name"], value=key)
            for key, translations in translator.translations.items()
            if current.lower() in key.lower()
        ][:25]

    @app_commands.command(
        name=app_commands.locale_str("timezone", key="timezone_param_name"),
        description=app_commands.locale_str("Set your timezone", key="timezone_command_description"),
    )
    @app_commands.rename(timezone=app_commands.locale_str("timezone", key="timezone_param_name"))
    @app_commands.describe(timezone=app_commands.locale_str("timezone", key="timezone_param_description"))
    async def set_timezone_command(self, i: Interaction, timezone: app_commands.Range[int, -12, 14]) -> None:
        await i.response.defer(ephemeral=True)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        user.timezone = timezone
        await user.save(update_fields=("timezone",))
        await self.bot.scheduler.schedule_reminder()

        embed = user.get_settings_saved_embed(await get_locale(i))
        await i.followup.send(embed=embed, ephemeral=True)


async def setup(bot: Lumina) -> None:
    await bot.add_cog(SettingsCog(bot))
