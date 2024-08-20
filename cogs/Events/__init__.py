from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import YukiSuou

from .base_events import DevEvents
from .wordism import Wordism


class Events(DevEvents, Wordism, name='Events'):
    def __init__(self, bot: YukiSuou) -> None:
        self.bot = bot


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(Events(bot))
