from __future__ import annotations

from typing import TYPE_CHECKING

from .waifu import Waifu

if TYPE_CHECKING:
    from bot import Lagrange


class Anime(Waifu, name='Anime & Manga'): ...


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Anime(bot))
