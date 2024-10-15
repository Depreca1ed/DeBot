from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import tasks

from utils import BaseCog

if TYPE_CHECKING:
    from bot import DeBot


class KitaKawa(BaseCog, name='KitaKawa'):
    def cog_load(self) -> None:
        self.mention_loop.start()

    def cog_unload(self) -> None:
        self.mention_loop.cancel()

    @tasks.loop(hours=6)
    async def mention_loop(self) -> None:
        ch = self.bot.get_channel(1277813689092804653)
        assert isinstance(ch, discord.TextChannel)
        if ch:
            await ch.send('<@&1295851367902089266> read kitakawa smh', allowed_mentions=discord.AllowedMentions.all())

async def setup(bot: DeBot) -> None:
    await bot.add_cog(KitaKawa(bot))
