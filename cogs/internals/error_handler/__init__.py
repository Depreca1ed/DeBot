from __future__ import annotations

import contextlib

import discord
from discord.ext import commands

from utils import BaseCog, DeContext, better_string
from utils.embed import Embed

from .constants import ERROR_COLOUR, HANDLER_EMOJIS
from .views import MissingArgumentHandler


class ErrorHandler(BaseCog):
    def clean_error_permission(self, permissions: list[str], *, seperator: str, prefix: str) -> str:
        return better_string(
            (prefix + (perm.replace('_', ' ')).capitalize() for perm in permissions),
            seperator=seperator,
        )

    def make_embed(self, *, title: str | None, description: str | None, ctx: DeContext | None = None) -> Embed:
        embed = Embed(title=title, description=description, ctx=ctx, colour=ERROR_COLOUR)
        embed.set_thumbnail(url=HANDLER_EMOJIS['MafuyuUnamused2'].url)
        return embed

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: DeContext, error: commands.CommandError) -> None:
        if (ctx.command and ctx.command.has_error_handler()) or (ctx.cog and ctx.cog.has_error_handler()):
            return

        if not ctx.command or isinstance(error, commands.CommandNotFound):
            with contextlib.suppress(discord.HTTPException):
                await ctx.message.add_reaction(str(HANDLER_EMOJIS['redtick']))
            return

        if isinstance(error, commands.MissingRequiredArgument | commands.MissingRequiredAttachment):
            param_name = (error.param.displayed_name or error.param.name).title()
            embed = self.make_embed(
                title=f'Missing {param_name} argument!',
                description=better_string(
                    (
                        f'You did not provide a **__{param_name}__** argument.',
                        f'> -# `{ctx.clean_prefix}{ctx.command} {ctx.command.signature}`',
                    ),
                    seperator='\n',
                ),
                ctx=ctx,
            )

            if isinstance(error, commands.MissingRequiredArgument):
                view = MissingArgumentHandler(error, ctx)
                view.prev_message = await ctx.reply(embed=embed, view=view)
                return

            await ctx.reply(embed=embed)
            return
