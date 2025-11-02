from __future__ import annotations

import os
from typing import TYPE_CHECKING

import aiohttp
from discord.ext import commands, tasks
from loguru import logger

if TYPE_CHECKING:
    from lumina.bot import Lumina


class HealthCheck(commands.Cog):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.send_heartbeat.start()

    async def cog_unload(self) -> None:
        self.send_heartbeat.cancel()

    @tasks.loop(minutes=1)
    async def send_heartbeat(self) -> None:
        url = os.getenv("HEARTBEAT_URL")
        if url is None:
            logger.warning("No heartbeat URL configured, skipping health check.")
            return

        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
                _ = await resp.read()
        except aiohttp.ClientError as e:
            logger.warning(f"Heartbeat request failed: {e}")
        except Exception:
            logger.exception("Unexpected error while sending heartbeat")

    @send_heartbeat.before_loop
    async def before_send_heartbeat(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: Lumina) -> None:
    await bot.add_cog(HealthCheck(bot))
