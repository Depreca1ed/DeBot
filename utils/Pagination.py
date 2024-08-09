from typing import Self

import discord
from discord.ext import commands

from bot import Elysian


class ElyPagination(discord.ui.View):
    message: discord.Message

    def __init__(
        self, embeds: list[discord.Embed], ctx: commands.Context[Elysian], *, has_timeout: bool | None = False
    ) -> None:
        if has_timeout and has_timeout is True:
            self.on_timeout = self.on_timeout_optional
            super().__init__(timeout=600)
        super().__init__()
        self.embeds = embeds
        self.ctx = ctx
        self.index = 0
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Requested by {self.ctx.author!s}" + " | " + f"Page {i+1} of {len(self.embeds)}")
        self._update_state()
        if not embeds or len(embeds) <= 1:
            self.first_page.disabled = self.prev_page.disabled = self.last_page.disabled = self.next_page.disabled = (
                self.remove.disabled
            ) = True
            self.stop()

    def _update_state(self) -> None:
        self.first_page.disabled = self.prev_page.disabled = self.index == 0
        self.last_page.disabled = self.next_page.disabled = self.index == len(self.embeds) - 1

    @discord.ui.button(emoji="<:emoji_8:1238879456115032065>", style=discord.ButtonStyle.grey)
    async def first_page(self, inter: discord.Interaction[Elysian], _: discord.ui.Button[discord.ui.View]) -> None:
        self.index = 0
        self._update_state()
        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(emoji="<:emoji_6:1238879362628059196>", style=discord.ButtonStyle.secondary)
    async def prev_page(self, inter: discord.Interaction[Elysian], _: discord.ui.Button[Self]) -> None:
        self.index -= 1
        self._update_state()
        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(emoji="<:emoji_9:1238879529662025748>", style=discord.ButtonStyle.grey)
    async def remove(self, inter: discord.Interaction[Elysian], _: discord.ui.Button[Self]) -> None:
        for child in (self.first_page, self.prev_page, self.remove, self.next_page, self.last_page):
            child.disabled = True
        await inter.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(emoji="<:emoji_7:1238879407830208593>", style=discord.ButtonStyle.secondary)
    async def next_page(self, inter: discord.Interaction[Elysian], _: discord.ui.Button[Self]) -> None:
        self.index += 1
        self._update_state()
        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(emoji="<:emoji_9:1238879493750394931>", style=discord.ButtonStyle.grey)
    async def last_page(self, inter: discord.Interaction[Elysian], _: discord.ui.Button[Self]) -> None:
        self.index = len(self.embeds) - 1
        self._update_state()
        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    async def on_timeout_optional(self) -> None:
        for child in (self.first_page, self.prev_page, self.remove, self.next_page, self.last_page):
            child.disabled = True
        await self.message.edit(view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message(
            "This is not your Interaction!",
            ephemeral=True,
        )
        return False
