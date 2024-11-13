from __future__ import annotations

from typing import TYPE_CHECKING

from .waifu import Waifu

if TYPE_CHECKING:
    from bot import DeBot


class AniManga(Waifu, name='Anime & Manga'): ...


async def setup(bot: DeBot) -> None:
    await bot.add_cog(AniManga(bot))
