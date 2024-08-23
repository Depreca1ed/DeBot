from __future__ import annotations

from typing import TYPE_CHECKING

from .botinfo import BotInformation
from .serverinfo import ServerInfo
from .userinfo import Userinfo

if TYPE_CHECKING:
    from bot import YukiSuou


class Info(BotInformation, Userinfo, ServerInfo, name='Info'):
    def __init__(self, bot: YukiSuou) -> None:
        super().__init__(bot)


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(Info(bot))
