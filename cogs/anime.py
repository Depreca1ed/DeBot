from __future__ import annotations

import contextlib
import datetime
from typing import TYPE_CHECKING, Self, cast

import discord
from aiohttp import ClientSession
from asyncpg.exceptions import UniqueViolationError
from discord import app_commands
from discord.ext import commands

from utils import WAIFU_TOKEN, Embed, Image, better_string

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from bot import Lagrange


class SmashOrPass(discord.ui.View):
    message: discord.Message
    current: Image

    def __init__(self, session: ClientSession, *, for_user: int, nsfw: bool) -> None:
        super().__init__(timeout=500.0)
        self.session = session
        self.for_user = for_user
        self.nsfw = nsfw

        self.smashers: set[discord.User | discord.Member] = set()
        self.passers: set[discord.User | discord.Member] = set()

    @classmethod
    async def start(cls, ctx: commands.Context[Lagrange]) -> Self:
        ctx.channel = cast(discord.TextChannel, ctx.channel)
        inst = cls(ctx.bot.session, for_user=ctx.author.id, nsfw=ctx.channel.nsfw)
        data = await inst.request()

        embed = inst.embed(data)
        inst.message = await ctx.reply(embed=embed, view=inst)

        return inst

    async def request(self) -> Image:
        raise NotImplementedError

    def embed(self, data: Image) -> discord.Embed:
        smasher = ', '.join(smasher.mention for smasher in self.smashers) if self.smashers else ''
        passer = ', '.join(passer.mention for passer in self.passers) if self.passers else ''

        embed = Embed(
            title='Smash or Pass',
            description=better_string(
                [
                    f'> [#{data["image_id"]}]({data["source"]})' if data['image_id'] and data['source'] else None,
                    '<:smash:1276874474628583497> **Smashers:** ' + smasher,
                    '<:pass:1276874515296813118> **Passers:** ' + passer,
                ],
                seperator='\n',
            ),
            colour=discord.Colour.from_str(data['dominant_color']) if data['dominant_color'] else None,
        )

        embed.set_image(url=data['url'])

        return embed

    @discord.ui.button(
        emoji='<:smash:1276874474628583497>',
        style=discord.ButtonStyle.green,
    )
    async def smash(self, interaction: discord.Interaction[Lagrange], _: discord.ui.Button[Self]) -> None:
        if interaction.user in self.smashers:
            interaction.channel = cast(discord.TextChannel, interaction.channel)
            try:
                await interaction.client.pool.execute(
                    """INSERT INTO WaifuFavourites VALUES ($1, $2, $3, $4)""",
                    self.current['url'],
                    interaction.user.id,
                    interaction.channel.is_nsfw(),
                    datetime.datetime.now(),
                )
            except UniqueViolationError:
                return await interaction.response.send_message(
                    'You have already added this waifu in your favourites list',
                    ephemeral=True,
                )
            return await interaction.response.send_message(
                f'Successfully added [#{self.current["image_id"]}](<{self.current["url"]}>)',
                ephemeral=True,
            )

        if interaction.user in self.passers:
            self.passers.remove(interaction.user)

        self.smashers.add(interaction.user)
        await interaction.response.edit_message(embed=self.embed(self.current))
        return None

    @discord.ui.button(
        emoji='<:pass:1276874515296813118>',
        style=discord.ButtonStyle.red,
    )
    async def passbutton(self, interaction: discord.Interaction[Lagrange], _: discord.ui.Button[Self]) -> None:
        if interaction.user in self.passers:
            return await interaction.response.defer()

        if interaction.user in self.smashers:
            self.smashers.remove(interaction.user)

        self.passers.add(interaction.user)
        await interaction.response.edit_message(embed=self.embed(self.current))
        return None

    @discord.ui.button(emoji='🔁', style=discord.ButtonStyle.grey)
    async def _next(self, interaction: discord.Interaction[Lagrange], _: discord.ui.Button[Self]) -> None:
        self.smashers.clear()
        self.passers.clear()

        data = await self.request()
        await interaction.response.edit_message(embed=self.embed(data))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.for_user:
            return True

        if (
            interaction.user.id != self.for_user
            and interaction.data
            and interaction.data['custom_id'] == self._next.custom_id  # pyright: ignore[reportGeneralTypeIssues]
        ):
            await interaction.response.send_message(
                'Only the command initiator can cycle through waifus in this message.',
                ephemeral=True,
            )

            return False

        return True

    async def on_timeout(self) -> None:
        with contextlib.suppress(discord.errors.NotFound):
            await self.message.edit(view=None)
        self.stop()


class WaifuView(SmashOrPass):
    async def request(self) -> Image:
        waifu = await self.session.get(
            'https://api.waifu.im/search',
            params={
                'is_nsfw': 'false' if self.nsfw is False else 'null',
                'token': WAIFU_TOKEN,
            },
        )

        data = await waifu.json()
        data = data['images'][0]
        current: Image = {
            'image_id': data['image_id'],
            'source': data['source'],
            'dominant_color': data['dominant_color'],
            'url': data['url'],
        }
        self.current = current

        return self.current


class SafebooruPokemonView(SmashOrPass):
    async def request(self) -> Image:
        waifu = await self.session.get(
            'https://safebooru.donmai.us/posts/random.json?tags=solo+pokemon_(creature)',
        )
        data = await waifu.json()
        current: Image = {
            'image_id': data['id'],
            'dominant_color': None,
            'source': data['source'],
            'url': data['file_url'],
        }
        self.current = current

        return self.current


class Anime(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    @commands.hybrid_command(name='waifu')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @commands.bot_has_permissions(external_emojis=True, embed_links=True, attach_files=True)
    async def waifu(self, ctx: commands.Context[Lagrange]) -> None:
        ctx.channel = cast(discord.TextChannel, ctx.channel)
        view = WaifuView(self.bot.session, for_user=ctx.author.id, nsfw=ctx.channel.is_nsfw())
        await view.start(ctx)

    @commands.hybrid_command(name='pokemon')
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @commands.bot_has_permissions(external_emojis=True, embed_links=True, attach_files=True)
    async def pokeemon(self, ctx: commands.Context[Lagrange]) -> None:
        view = SafebooruPokemonView(self.bot.session, for_user=ctx.author.id, nsfw=False)
        await view.start(ctx)


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Anime(bot))
