from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

import anyio
import discord
from discord.ext import commands
from discord.utils import sleep_until
from loguru import logger
from tortoise import Tortoise

from lumina.command_tree import CommandTree
from lumina.constants import DEFAULT_LOCALE
from lumina.error_handler import create_error_embed
from lumina.l10n import AppCommandTranslator, translator
from lumina.models import Reminder

if TYPE_CHECKING:
    from lumina.embeds import ErrorEmbed


class ReminderScheduler:
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot
        self.current_task: asyncio.Task | None = None

    async def send_reminder(self, reminder: Reminder) -> None:
        logger.info(f"Sending reminder to {reminder.user_id}")
        embed = reminder.get_embed(reminder.user.locale or DEFAULT_LOCALE)
        success = await self.bot.dm_user(reminder.user_id, embed=embed)
        if success:
            await reminder.delete()
        else:
            reminder.sent = True
            await reminder.save()

    async def get_next_reminder(self) -> Reminder | None:
        return await Reminder.filter(sent=False).order_by("datetime").first().prefetch_related("user")

    async def sleep_task(self, reminder: Reminder) -> None:
        await sleep_until(reminder.datetime)
        await self.send_reminder(reminder)
        self.current_task = None
        await self.schedule_reminder()

    async def schedule_reminder(self) -> None:
        self.cancel_task()

        reminder = await self.get_next_reminder()
        logger.debug(f"Next reminder: {reminder}")
        if reminder is None:
            return

        self.current_task = asyncio.create_task(self.sleep_task(reminder))

    def cancel_task(self) -> None:
        if self.current_task is not None:
            self.current_task.cancel()
            self.current_task = None


class Lumina(commands.Bot):
    def __init__(self) -> None:
        self.scheduler = ReminderScheduler(self)

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents(emojis=True, messages=True, guilds=True),
            allowed_contexts=discord.app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
            allowed_installs=discord.app_commands.AppInstallationType(guild=True, user=True),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            help_command=None,
            chunk_guilds_at_startup=False,
            max_messages=None,  # pyright: ignore[reportArgumentType]
            member_cache_flags=discord.MemberCacheFlags.none(),
            tree_cls=CommandTree,
        )

    async def _setup_database(self) -> None:
        await Tortoise.init(db_url="sqlite://lumina.db", modules={"models": ["lumina.models"]}, use_tz=True)
        await Tortoise.generate_schemas()

    async def _setup_translator(self) -> None:
        await translator.load()

    async def _load_cogs(self) -> None:
        async for filepath in anyio.Path("lumina/cogs").glob("**/*.py"):
            cog_name = anyio.Path(filepath).stem
            if os.getenv("ENV", "dev") == "dev" and cog_name == "health":
                continue

            try:
                await self.load_extension(f"lumina.cogs.{cog_name}")
                logger.info(f"Loaded cog {cog_name}")
            except Exception:
                logger.exception(f"Failed to load cog {cog_name}")

        try:
            await self.load_extension("jishaku")
        except Exception:
            logger.exception("Failed to load jishaku")
        else:
            logger.info("Loaded jishaku")

    async def setup_hook(self) -> None:
        await self._setup_database()
        await self._setup_translator()
        await self._load_cogs()

        await self.tree.set_translator(AppCommandTranslator())
        await self.scheduler.schedule_reminder()

    def create_error_embed(self, error: Exception, *, locale: discord.Locale) -> tuple[ErrorEmbed, bool]:
        return create_error_embed(error, locale=locale)

    async def dm_user(self, user_id: int, *, embed: discord.Embed) -> bool:
        try:
            user = await self.fetch_user(user_id)
        except discord.NotFound:
            logger.warning(f"Could not find user with ID {user_id}.")
            return False

        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"Could not DM {user}.")
            return False

        return True

    async def close(self) -> None:
        await Tortoise.close_connections()
        return await super().close()
