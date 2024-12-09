from __future__ import annotations

import contextlib
from typing import Self

import discord
from discord.ext import commands

from bot import DeBot
from utils import BaseCog, BaseView, DeContext, better_string

CHAR_LIMIT = 2000

HANDLER_EMOJIS = {'redTick': '<a:redtick:1315758805585498203>', 'greyTick': '<:grey_tick:1278414780427796631>'}


class MissingArgumentHandler(BaseView):
    def __init__(self, error: commands.MissingRequiredArgument, ctx: DeContext, *, timeout: float | None = 180):
        self.error = error
        self.ctx = ctx
        self.argument_button.label = f'Add {self.error.param.displayed_name or self.error.param.name}'
        super().__init__(timeout=timeout)

    @discord.ui.button(emoji=HANDLER_EMOJIS['greyTick'], style=discord.ButtonStyle.grey)
    async def argument_button(self, interaction: discord.Interaction[DeBot], _: discord.Button[Self]):
        pass


class ErrorHandler(BaseCog):
    def clean_error_permission(self, permissions: list[str], *, seperator: str, prefix: str) -> str:
        return better_string(
            (prefix + (perm.replace('_', ' ')).capitalize() for perm in permissions),
            seperator=seperator,
        )

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: DeContext, error: commands.CommandError) -> None:
        if (ctx.command and ctx.command.has_error_handler()) or (ctx.cog and ctx.cog.has_error_handler()):
            return
        if not ctx.command or isinstance(error, commands.CommandNotFound):
            with contextlib.suppress(discord.HTTPException):
                await ctx.message.add_reaction(HANDLER_EMOJIS['redTick'])
            return
        if isinstance(error, commands.MissingRequiredArgument):
            pass
