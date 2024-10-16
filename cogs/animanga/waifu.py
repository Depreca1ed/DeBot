from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands
from discord.ext import commands

from utils import BaseCog

from .views import SafebooruPokemonView, WaifuView, WaifuViewBackup

if TYPE_CHECKING:
    from utils import DeContext

__all__ = ('Waifu',)


class Waifu(BaseCog):
    @commands.hybrid_group(name='waifu', help='Get waifu images with an option to smash or pass')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def waifu(self, ctx: DeContext) -> None:
        await ctx.invoke(self.waifu_show)

    @waifu.command(name='favourites', with_app_command=False)
    @commands.is_owner()
    async def waifu_favourites(self, ctx: DeContext) -> None:
        await ctx.reply('test')

    @waifu.command(
        name='show',
        hidden=True,
        help='Get waifu images with an option to smash or pass',
    )
    async def waifu_show(self, ctx: DeContext) -> None:
        ctx.channel = cast(discord.TextChannel, ctx.channel)
        try:
            view = WaifuView(self.bot.session, for_user=ctx.author.id, nsfw=False, source='waifu')
            await view.start(ctx, 'waifu')
        except KeyError:
            view = WaifuViewBackup(
                self.bot.session,
                for_user=ctx.author.id,
                nsfw=ctx.channel.is_nsfw(),
                source='waifu',
            )
            await view.start(ctx, 'waifu')

    @commands.hybrid_command(name='pokemon', help='Get pokemon images with an option to smash or pass')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def pokemon(self, ctx: DeContext) -> None:
        view = SafebooruPokemonView(self.bot.session, for_user=ctx.author.id, nsfw=False, source='pokemon')
        await view.start(ctx, 'pokemon')
