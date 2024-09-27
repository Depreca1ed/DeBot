from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils import BaseCog, Embed

if TYPE_CHECKING:
    from utils import LagContext


class Avatar(BaseCog):
    @commands.hybrid_group(name='avatar', help="Get your or user's displayed avatar", aliases=['av'])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def avatar(self, ctx: LagContext, user: discord.User | discord.Member | None) -> discord.Message:
        user_ = user or ctx.author
        embed = Embed(title=f"{user_}'s avatar", colour=user_.color, ctx=ctx).set_image(url=user_.display_avatar.url)
        filetypes = (
            discord.asset.VALID_STATIC_FORMATS
            if user_.display_avatar.is_animated() is False
            else discord.asset.VALID_ASSET_FORMATS
        )
        filetypes = set(filetypes)
        filetypes.discard("jpg")
        view = discord.ui.View()
        comps: list[discord.ui.Button[discord.ui.View]] = [
            discord.ui.Button(
                label=ft.upper(),
                style=discord.ButtonStyle.url,
                url=user_.display_avatar.with_format('png').url,
            )
            for ft in filetypes
        ]
        for comp in comps:
            view.add_item(comp)
        return await ctx.send(embed=embed, view=view)

    @avatar.command(
        name='show',
        help=avatar.help,
    )  # This is supposed to basically be the slash for avatar command since group base are not really created as a slash command
    async def avatar_slash(self, ctx: LagContext, user: discord.User | discord.Member | None) -> discord.Message:
        return await ctx.invoke(self.avatar, user)

    @avatar.command(name='user', help="Get your or user's profile avatar. This does not include server avatars")
    async def avatar_norm(self, ctx: LagContext, user: discord.User | None) -> discord.Message:
        user_ = user or ctx.author
        av = user_.avatar or user_.default_avatar
        embed = Embed(title=f"{user_}'s avatar", ctx=ctx).set_image(url=av.url)
        filetypes = discord.asset.VALID_STATIC_FORMATS if av.is_animated() is False else discord.asset.VALID_ASSET_FORMATS
        filetypes = set(filetypes)
        filetypes.discard("jpg")
        view = discord.ui.View()
        comps: list[discord.ui.Button[discord.ui.View]] = [
            discord.ui.Button(
                label=ft.upper(),
                style=discord.ButtonStyle.url,
                url=av.with_format('png').url,
            )
            for ft in filetypes
        ]
        for comp in comps:
            view.add_item(comp)
        return await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='icon', help="Get the server's icon, if any")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    @commands.guild_only()
    async def guild_avatar(self, ctx: LagContext) -> discord.Message:
        assert ctx.guild is not None
        icon = ctx.guild.icon
        if not icon:
            return await ctx.reply(content=f'{commands.clean_content().convert(ctx, str(ctx.guild))} does not have an icon.')
        embed = Embed(title=f"{ctx.guild}'s icon", ctx=ctx).set_image(url=icon.url)
        filetypes = discord.asset.VALID_STATIC_FORMATS if icon.is_animated() is False else discord.asset.VALID_ASSET_FORMATS
        filetypes = set(filetypes)
        filetypes.discard("jpg")
        view = discord.ui.View()
        comps: list[discord.ui.Button[discord.ui.View]] = [
            discord.ui.Button(
                label=ft.upper(),
                style=discord.ButtonStyle.url,
                url=icon.with_format('png').url,
            )
            for ft in filetypes
        ]
        for comp in comps:
            view.add_item(comp)
        return await ctx.send(embed=embed, view=view)
