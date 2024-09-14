from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands
from discord.ext import commands

from .views import SafebooruPokemonView, WaifuView, WaifuViewBackup

if TYPE_CHECKING:
    from bot import Lagrange
    from utils import LagContext

__all__ = ('Waifu',)


class Waifu(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    @commands.hybrid_group(name='waifu')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def waifu(self, ctx: LagContext) -> None:
        await ctx.invoke(self.waifu_show)

    @waifu.command(name='favourites')
    async def waifu_favourites(self, ctx: LagContext) -> None:
        await ctx.reply('test')

    @waifu.command(name='show', hidden=True)
    async def waifu_show(self, ctx: LagContext) -> None:
        ctx.channel = cast(discord.TextChannel, ctx.channel)
        try:
            view = WaifuView(self.bot.session, for_user=ctx.author.id, nsfw=False, source='waifu')
            await view.start(ctx, 'waifu')
        except KeyError:
            view = WaifuViewBackup(self.bot.session, for_user=ctx.author.id, nsfw=ctx.channel.is_nsfw(), source='waifu')
            await view.start(ctx, 'waifu')

    @commands.hybrid_command(name='pokemon')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def pokemon(self, ctx: LagContext) -> None:
        view = SafebooruPokemonView(self.bot.session, for_user=ctx.author.id, nsfw=False, source='pokemon')
        await view.start(ctx, 'pokemon')
