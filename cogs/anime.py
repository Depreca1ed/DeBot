from __future__ import annotations

from typing import TYPE_CHECKING, Self

import discord
from discord import app_commands
from discord.ext import commands

from utils import WAIFU_TOKEN, Embed, Waifu, WaifuImage, better_string

if TYPE_CHECKING:
    from bot import Lagrange


class WaifuView(discord.ui.View):
    message: discord.Message
    current: WaifuImage

    def __init__(self, ctx: commands.Context[Lagrange]) -> None:
        super().__init__(timeout=500.0)
        self.ctx: commands.Context[Lagrange] = ctx
        self.smashers: list[discord.User | discord.Member] = []
        self.passers: list[discord.User | discord.Member] = []

    async def start(self) -> None:
        data = await self.request()
        embed = self.embed(data)
        self.message = await self.ctx.reply(embed=embed, view=self)

    async def request(self) -> WaifuImage:
        waifu = await self.ctx.bot.session.get(
            'https://api.waifu.im/search',
            params={
                'is_nsfw': 'false',
                'token': WAIFU_TOKEN,
            },
        )
        data: Waifu = await waifu.json()
        self.current = data['images'][0]
        return self.current

    def embed(self, data: WaifuImage) -> discord.Embed:
        embed = Embed(
            title='Smash or Pass',
            description=better_string(
                [
                    f'> [#{data["image_id"]}]({data["source"]})',
                    f'<:smash:1276874474628583497> **Smashers :** `{len(self.smashers)}`',
                    f'<:pass:1276874515296813118> **Passers :** `{len(self.passers)}`',
                ],
                seperator='\n',
            ),
            colour=discord.Colour.from_str(data['dominant_color']),
            ctx=self.ctx,
        )
        embed.set_image(url=data['url'])
        return embed

    @discord.ui.button(
        emoji='<:smash:1276874474628583497>',
        style=discord.ButtonStyle.green,
    )
    async def smash(self, interaction: discord.Interaction[Lagrange], _: discord.ui.Button[Self]) -> None:
        if interaction.user in self.passers:
            self.passers.remove(interaction.user)
        if interaction.user in self.smashers:
            return await interaction.response.send_message(
                embed=Embed(
                    title='Smashers',
                    description=better_string([str(user for user in self.smashers)], seperator=','),
                    ctx=self.ctx,
                ),
            )
        self.smashers.append(interaction.user)
        return await interaction.response.edit_message(embed=self.embed(self.current))

    @discord.ui.button(
        emoji='<:pass:1276874515296813118>',
        style=discord.ButtonStyle.red,
    )
    async def passbutton(self, interaction: discord.Interaction[Lagrange], _: discord.ui.Button[Self]) -> None:
        if interaction.user in self.smashers:
            self.smashers.remove(interaction.user)
        if interaction.user in self.passers:
            return await interaction.response.send_message(
                embed=Embed(
                    title='Passers',
                    description=better_string([str(user for user in self.passers)], seperator=','),
                    ctx=self.ctx,
                ),
            )
        self.passers.append(interaction.user)
        return await interaction.response.edit_message(embed=self.embed(self.current))

    @discord.ui.button(emoji='🔁', style=discord.ButtonStyle.grey)
    async def loopit(self, interaction: discord.Interaction[Lagrange], _: discord.ui.Button[Self]) -> None:
        self.smashers.clear()
        self.passers.clear()
        data = await self.request()
        embed = self.embed(data)
        return await interaction.response.edit_message(embed=embed)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id and interaction.data['custom_id'] == self.loopit.custom_id:  # type: ignore[reportGeneralTypeIssues]
            await interaction.response.send_message(
                'Only the command initiator can cycle through waifus in this message.',
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)
        self.stop()


class Anime(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    @commands.hybrid_command(name='waifu')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @commands.bot_has_permissions(external_emojis=True, embed_links=True, attach_files=True)
    async def waifu(self, ctx: commands.Context[Lagrange]) -> None:
        view = WaifuView(ctx)
        await view.start()


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Anime(bot))
