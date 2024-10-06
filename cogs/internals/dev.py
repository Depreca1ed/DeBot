from __future__ import annotations

from pkgutil import iter_modules

from discord.ext import commands

from utils import BaseCog, DeContext, better_string


class Developer(BaseCog):
    @commands.command(name='reload', aliases=['re'], hidden=True)
    async def reload_cogs(self, ctx: DeContext) -> None:
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
