from __future__ import annotations

from typing import TYPE_CHECKING

from .botinfo import BotInformation
from .serverinfo import ServerInfo
from .userinfo import Userinfo

if TYPE_CHECKING:
    from bot import Lagrange


class Info(BotInformation, Userinfo, ServerInfo, name='Info'):
    def __init__(self, bot: Lagrange) -> None:
        super().__init__(bot)


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Info(bot))
