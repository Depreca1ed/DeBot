from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from bot import Lagrange


class BaseCog(commands.Cog):
    bot: Lagrange

    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot
