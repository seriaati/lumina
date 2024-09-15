from __future__ import annotations

from typing import TypeAlias

import discord

from lumina.bot import Lumina

Interaction: TypeAlias = discord.Interaction[Lumina]
UserOrMember: TypeAlias = discord.User | discord.Member
