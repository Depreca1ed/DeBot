from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from bot import YukiSuou


class Dev(commands.Cog):
    def __init__(self, bot: YukiSuou) -> None:
        self.bot: YukiSuou = bot

    async def cog_check(self, ctx: commands.Context[YukiSuou]) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await self.bot.is_owner(ctx.author) and ctx.prefix != ""


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(Dev(bot))
