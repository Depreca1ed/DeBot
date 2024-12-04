from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import DeBot
    from utils import DeContext
import contextlib

import discord
import starlight
from discord.ext import commands

from .dev import Developer
from .error_handler import ErrorHandler


class Events(ErrorHandler, Developer, name='Events'):
    def cog_load(self) -> None:
        self.bot.help_command = starlight.MenuHelpCommand(
            per_page=10, accent_color=self.bot.colour, error_color=discord.Color.red()
        )

    def cog_unload(self) -> None:
        self.bot.help_command = commands.DefaultHelpCommand()

    @discord.utils.copy_doc(commands.Cog.cog_check)
    async def cog_check(self, ctx: DeContext) -> bool:
        return await self.bot.is_owner(ctx.author)

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


async def setup(bot: DeBot) -> None:
    await bot.add_cog(Events(bot))
