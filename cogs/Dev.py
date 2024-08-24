from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from bot import Lagrange


class Dev(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot: Lagrange = bot

    async def cog_check(self, ctx: commands.Context[Lagrange]) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await self.bot.is_owner(ctx.author) and ctx.prefix != ''


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Dev(bot))
