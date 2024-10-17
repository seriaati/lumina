from __future__ import annotations

import discord

from lumina.bot import Lumina

type Interaction = discord.Interaction[Lumina]
type UserOrMember = discord.User | discord.Member
