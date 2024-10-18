from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from utils import BaseCog

if TYPE_CHECKING:
    from bot import DeBot


class KitaKawa(BaseCog, name='KitaKawa'):
    def cog_load(self) -> None:
        self.mention_loop.start()

    def cog_unload(self) -> None:
        self.mention_loop.cancel()

    @tasks.loop(hours=4)
    async def mention_loop(self) -> None:
        ch = self.bot.get_channel(1277813689092804653)
        if ch:
            assert isinstance(ch, discord.TextChannel)
            await ch.send(
                '<@&1295851367902089266> read kitakawa smh',
                allowed_mentions=discord.AllowedMentions.all(),
            )

    @commands.Cog.listener('on_raw_reaction_add')
    async def yoshimi_filter(self, payload: discord.RawReactionActionEvent) -> None:
        ch = self.bot.get_channel(1277894451850776616)
        if (
            ch
            and ch.id == payload.channel_id
            and payload.event_type == 'REACTION_ADD'
            and payload.member
            and str(payload.emoji) == '<:YoshimiCreepy:1277968074062168064>'
            and payload.message_id == 1278029325765185588
        ):
            with contextlib.suppress(discord.HTTPException):
                await payload.member.kick(reason='Yoshimis are bad')


async def setup(bot: DeBot) -> None:
    await bot.add_cog(KitaKawa(bot))
