from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands
from discord.ext import commands

from utils import BaseCog

from .views import SafebooruPokemonView, WaifuSearchView, WaifuView

if TYPE_CHECKING:
    from bot import DeBot
    from utils import DeContext

__all__ = ('Waifu',)

CHARACTER_ID = 4


async def waifu_autocomplete(
    interaction: discord.Interaction[DeBot],
    current: str,
) -> list[app_commands.Choice[str]]:
    req = await interaction.client.session.get(
        'https://safebooru.donmai.us/autocomplete.json',
        params={
            'search[query]': current,
            'search[type]': 'tag_query',
        },
    )
    data = await req.json()
    characters = [(str(obj['label']), str(obj['value'])) for obj in data if obj['category'] == CHARACTER_ID]
    return [app_commands.Choice(name=char[0].title(), value=char[1]) for char in characters]


class Waifu(BaseCog):
    @commands.hybrid_group(name='waifu', help='Get waifu images with an option to smash or pass')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def waifu(self, ctx: DeContext, waifu: str | None) -> None:
        if waifu:
            req = await ctx.bot.session.get(
                'https://safebooru.donmai.us/autocomplete.json',
                params={
                    'search[query]': waifu,
                    'search[type]': 'tag_query',
                },
            )
            data = await req.json()
            characters = [(str(obj['label']), str(obj['value'])) for obj in data if obj['category'] == CHARACTER_ID]
            waifu = characters[0][1]  # Points to the value of the first result

        await ctx.invoke(self.waifu_show, waifu)

    @waifu.command(name='favourites', with_app_command=False)
    @commands.is_owner()
    async def waifu_favourites(self, ctx: DeContext) -> None:
        await ctx.reply('test')

    @waifu.command(
        name='show',
        hidden=True,
        help='Get waifu images with an option to smash or pass',
    )
    @app_commands.autocomplete(waifu=waifu_autocomplete)
    async def waifu_show(self, ctx: DeContext, waifu: str | None) -> None:
        ctx.channel = cast(discord.TextChannel, ctx.channel)
        if waifu:
            view = WaifuSearchView(
                self.bot.session,
                for_user=ctx.author.id,
                nsfw=ctx.channel.is_nsfw()
                if not isinstance(ctx.channel, discord.DMChannel | discord.GroupChannel | discord.PartialMessageable)
                else False,
                source='waifusearch',
                query=waifu,
            )
            await view.start(ctx, 'waifusearch', query=waifu)
            return
        view = WaifuView(
            self.bot.session,
            for_user=ctx.author.id,
            nsfw=ctx.channel.is_nsfw()
            if not isinstance(ctx.channel, discord.DMChannel | discord.GroupChannel | discord.PartialMessageable)
            else False,
            source='waifu',
        )
        await view.start(ctx, 'waifu', query=waifu)

    @commands.hybrid_command(name='pokemon', help='Get pokemon images with an option to smash or pass')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def pokemon(self, ctx: DeContext) -> None:
        ctx.channel = cast(discord.TextChannel, ctx.channel)
        view = SafebooruPokemonView(
            self.bot.session,
            for_user=ctx.author.id,
            nsfw=ctx.channel.is_nsfw()
            if not isinstance(ctx.channel, discord.DMChannel | discord.GroupChannel | discord.PartialMessageable)
            else False,
            source='pokemon',
        )
        await view.start(ctx, 'pokemon')
