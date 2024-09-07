from __future__ import annotations

from typing import TYPE_CHECKING

from .waifu import Waifu

if TYPE_CHECKING:
    from bot import Lagrange


class Anime(Waifu, name='Anime'):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Anime(bot))
