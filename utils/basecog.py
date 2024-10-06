from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from bot import DeBot


class BaseCog(commands.Cog):
    bot: DeBot

    def __init__(self, bot: DeBot) -> None:
        self.bot = bot
