from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from lumina.l10n import translator

if TYPE_CHECKING:
    from lumina.bot import Lumina


class AdminCog(commands.Cog):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="sync")
    async def sync_command(self, ctx: commands.Context) -> None:
        message = await ctx.send("Syncing commands...")
        synced_commands = await self.bot.tree.sync()
        await message.edit(content=f"Synced {len(synced_commands)} commands.")

    @commands.command(name="reload-translator", aliases=["rt"])
    async def reload_translator_command(self, ctx: commands.Context) -> None:
        await translator.load()
        await ctx.send("Reloaded translator.")


async def setup(bot: Lumina) -> None:
    await bot.add_cog(AdminCog(bot))
