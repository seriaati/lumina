from __future__ import annotations

import asyncio
import pathlib
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from loguru import logger
from tortoise import Tortoise

from lumina.command_tree import CommandTree
from lumina.constants import DEFAULT_LOCALE
from lumina.error_handler import create_error_embed
from lumina.l10n import AppCommandTranslator, Translator
from lumina.models import Reminder
from lumina.utils import get_now

if TYPE_CHECKING:
    from lumina.embeds import ErrorEmbed


class ReminderScheduler:
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot
        self.current_task: asyncio.Task | None = None

    async def send_reminder(self, reminder: Reminder) -> None:
        logger.info(f"Sending reminder to {reminder.user_id}")
        embed = reminder.get_embed(self.bot.translator, reminder.user.locale or DEFAULT_LOCALE)
        success = await self.bot.dm_user(reminder.user_id, embed=embed)
        if success:
            await reminder.delete()

    async def get_next_reminder(self) -> Reminder | None:
        return await Reminder.all().order_by("datetime").first().prefetch_related("user")

    async def sleep_task(self, reminder: Reminder) -> None:
        now = get_now(reminder.user.timezone)
        await asyncio.sleep((reminder.datetime - now).total_seconds())
        await self.send_reminder(reminder)

    async def schedule_reminder(self) -> None:
        self.cancel_task()

        reminder = await self.get_next_reminder()
        if reminder is None:
            return

        self.current_task = asyncio.create_task(self.sleep_task(reminder))

    def cancel_task(self) -> None:
        if self.current_task is not None:
            self.current_task.cancel()
            self.current_task = None


class Lumina(commands.Bot):
    def __init__(self) -> None:
        self.translator = Translator()
        self.scheduler = ReminderScheduler(self)

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents(emojis=True, messages=True, guilds=True),
            allowed_contexts=discord.app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
            allowed_installs=discord.app_commands.AppInstallationType(guild=True, user=True),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            help_command=None,
            chunk_guilds_at_startup=False,
            max_messages=None,
            member_cache_flags=discord.MemberCacheFlags.none(),
            tree_cls=CommandTree,
        )

    async def _setup_database(self) -> None:
        await Tortoise.init(
            db_url="sqlite://lumina.db", modules={"models": ["lumina.models"]}, timezone="UTC"
        )
        await Tortoise.generate_schemas()

    async def _setup_translator(self) -> None:
        await self.translator.load()

    async def _load_cogs(self) -> None:
        for file_path in pathlib.Path("./lumina/cogs").rglob("*.py"):
            if file_path.stem == "__init__":
                continue

            cog_path = ".".join(file_path.with_suffix("").parts)
            try:
                await self.load_extension(cog_path)
            except Exception:
                logger.exception(f"Failed to load cog {cog_path}")
            else:
                cog_name = cog_path.split(".")[-1]
                logger.info(f"Loaded cog {cog_name!r}")

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

        await self.tree.set_translator(AppCommandTranslator(self.translator))
        await self.scheduler.schedule_reminder()

    def create_error_embed(
        self, error: Exception, *, locale: discord.Locale
    ) -> tuple[ErrorEmbed, bool]:
        return create_error_embed(error, translator=self.translator, locale=locale)

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
