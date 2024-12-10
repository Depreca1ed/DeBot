from __future__ import annotations

import contextlib
from typing import Self

import discord
from discord.ext import commands

from bot import DeBot
from utils import BaseCog, BaseView, DeContext, better_string

CHAR_LIMIT = 2000

HANDLER_EMOJIS = {'redTick': '<a:redtick:1315758805585498203>', 'greyTick': '<:grey_tick:1278414780427796631>'}


class MissingArgumentModal(discord.ui.Modal):
    prev_message: discord.Message
    argument: discord.ui.TextInput[MissingArgumentHandler] = discord.ui.TextInput(
        label='Add the missing argument',
        style=discord.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        max_length=300,
    )

    def __init__(
        self,
        error: commands.MissingRequiredArgument,
        ctx: DeContext,
        *,
        title: str,
        timeout: float | None = None,
        custom_id: str = discord.utils.MISSING,
    ) -> None:
        self.error = error
        self.ctx = ctx
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        cmd = self.ctx.command
        if not cmd:
            await interaction.response.send_message('Something went wrong', ephemeral=True)
            return self.ctx.bot.dispatch(
                'command_error', self.ctx, commands.CommandError(message='Command in Missing Argument Modal was None')
            )
        msg_content = self.ctx.message.content
        new_content = f'{msg_content} {self.argument.value}'
        self.ctx.message.content = new_content
        await self.ctx.bot.process_commands(self.ctx.message)
        await self.prev_message.delete()
        return await interaction.response.defer()


class MissingArgumentHandler(BaseView):
    prev_message: discord.Message

    def __init__(self, error: commands.MissingRequiredArgument, ctx: DeContext, *, timeout: float | None = 180) -> None:
        self.error = error
        self.ctx = ctx
        super().__init__(timeout=timeout)
        self.argument_button.label = f'Add {self.error.param.displayed_name or self.error.param.name}'

    @discord.ui.button(emoji=HANDLER_EMOJIS['greyTick'], style=discord.ButtonStyle.grey)
    async def argument_button(self, interaction: discord.Interaction[DeBot], _: discord.ui.Button[Self]) -> None:
        modal = MissingArgumentModal(self.error, self.ctx, title=self.error.param.displayed_name or self.error.param.name)
        modal.prev_message = self.prev_message
        await interaction.response.send_modal(modal)


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
            view = MissingArgumentHandler(error, ctx)
            view.prev_message = await ctx.reply(content=str(error), view=view)
            return
