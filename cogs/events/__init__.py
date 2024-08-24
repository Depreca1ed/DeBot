from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Lagrange
import contextlib

import discord
from discord.ext import commands

from .errors import Errors


class Events(Errors, name='Events'):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    @commands.Cog.listener('on_message_edit')
    async def edit_mechanic(self, _: discord.Message, after: discord.Message) -> None:
        if await self.bot.is_owner(after.author):
            await self.bot.process_commands(after)

    @commands.Cog.listener('on_reaction_add')
    async def delete_message(self, reaction: discord.Reaction, user: discord.Member | discord.User) -> None:
        if (
            await self.bot.is_owner(user)
            and reaction.emoji
            and reaction.emoji == '🗑️'
            and reaction.message.author.id == self.bot.user.id
        ):
            with contextlib.suppress(discord.HTTPException):
                await reaction.message.delete()


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Events(bot))
