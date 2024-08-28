from __future__ import annotations

from pkgutil import iter_modules
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from utils import LagContext, better_string

if TYPE_CHECKING:
    from bot import Lagrange


class Dev(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot: Lagrange = bot

    @discord.utils.copy_doc(commands.Cog.cog_check)
    async def cog_check(self, ctx: LagContext) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.command(name='reload', aliases=['re'])
    async def reload_cogs(self, ctx: LagContext) -> None:
        cogs = [m.name for m in iter_modules(['cogs'], prefix='cogs.')]
        messages: list[str] = []
        for cog in cogs:
            try:
                await self.bot.reload_extension(str(cog))
            except commands.ExtensionError as error:
                messages.append(f'Failed to reload {cog}\n```py{error}```')
            else:
                messages.append(f'Reloaded {cog}')
        await ctx.send(content=better_string(messages, seperator='\n'))


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Dev(bot))
