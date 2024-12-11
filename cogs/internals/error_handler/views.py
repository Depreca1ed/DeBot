from __future__ import annotations

import contextlib
import copy
from typing import TYPE_CHECKING, Self

import discord

from utils import BaseView, DeContext

from .constants import HANDLER_EMOJIS

if TYPE_CHECKING:
    from discord.ext import commands

    from bot import DeBot


class MissingArgumentModal(discord.ui.Modal):
    argument: discord.ui.TextInput[MissingArgumentHandler] = discord.ui.TextInput(
        label='Enter the Missing Argument,',
        style=discord.TextStyle.long,
        placeholder='...',
        required=True,
        max_length=2000,
    )

    def __init__(
        self,
        error: commands.MissingRequiredArgument,
        ctx: DeContext,
        *,
        title: str,
        timeout: float | None = None,
        previous_message: discord.Message,
    ) -> None:
        self.error = error
        self.ctx = ctx
        self.prev_message = previous_message
        super().__init__(title=title, timeout=timeout)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        cmd = self.ctx.command
        if not cmd:
            await interaction.response.send_message('Something went wrong', ephemeral=True)
            msg = 'Command not found. This should not happen.'
            raise TypeError(msg)
        new_context = copy.copy(self.ctx)
        new_context.message.content = f'{self.ctx.message.content} {self.argument.value}'

        await self.ctx.bot.process_commands(new_context.message)

        with contextlib.suppress(discord.HTTPException):
            await self.prev_message.delete()

        return await interaction.response.defer()


class MissingArgumentHandler(BaseView):
    prev_message: discord.Message

    def __init__(self, error: commands.MissingRequiredArgument, ctx: DeContext, *, timeout: float | None = 180) -> None:
        self.error = error
        self.ctx = ctx
        super().__init__(timeout=timeout)
        self.argument_button.label = f'Add {(self.error.param.displayed_name or self.error.param.name).title()}'

    @discord.ui.button(emoji=HANDLER_EMOJIS['grey_tick'], style=discord.ButtonStyle.grey)
    async def argument_button(self, interaction: discord.Interaction[DeBot], _: discord.ui.Button[Self]) -> None:
        modal = MissingArgumentModal(
            self.error,
            self.ctx,
            title=self.error.param.displayed_name or self.error.param.name,
            previous_message=self.prev_message,
        )
        modal.prev_message = self.prev_message
        await interaction.response.send_modal(modal)
