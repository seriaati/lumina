from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys

import discord
from dotenv import load_dotenv
from loguru import logger

from lumina.bot import Lumina
from lumina.logging import InterceptHandler


def setup_logger() -> None:
    discord.VoiceClient.warn_nacl = False
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
    logger.add("logs/lumina.log", rotation="1 week", retention="1 month", level="INFO")


async def main() -> None:
    async with Lumina() as bot:
        await bot.start(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    load_dotenv()
    setup_logger()

    with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
        asyncio.run(main())
