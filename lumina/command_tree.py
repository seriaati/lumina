from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import discord
from loguru import logger

from lumina.error_handler import create_error_embed
from lumina.utils import absolute_send

if TYPE_CHECKING:
    from lumina.types import Interaction


class CommandTree(discord.app_commands.CommandTree):
    async def on_error(self, i: Interaction, e: discord.app_commands.AppCommandError) -> None:
        error = e.original if isinstance(e, discord.app_commands.CommandInvokeError) else e

        if isinstance(error, discord.app_commands.CheckFailure):
            return

        embed, recognized = create_error_embed(error, translator=i.client.translator, locale=i.locale)
        if not recognized:
            logger.exception("An unrecognized error occurred.")

        with contextlib.suppress(discord.NotFound):
            await absolute_send(i, embed=embed, ephemeral=True)
