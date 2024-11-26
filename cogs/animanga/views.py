from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Self, cast

import discord
from asyncpg.exceptions import UniqueViolationError

from utils import BaseView, DeContext, Embed, Image, better_string

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from bot import DeBot


__all__ = ('WaifuView', 'SafebooruPokemonView', 'WaifuViewBackup')


class SmashOrPass(BaseView):
    message: discord.Message
    current: Image

    def __init__(self, token: str, session: ClientSession, *, for_user: int, nsfw: bool, source: str) -> None:
        super().__init__(timeout=500.0)
        self.session = session
        self.for_user = for_user
        self.nsfw = nsfw
        self.source = source
        self.token = token

        self.smashers: set[discord.User | discord.Member] = set()
        self.passers: set[discord.User | discord.Member] = set()

    @classmethod
    async def start(cls, ctx: DeContext, source: str) -> Self:
        inst = cls(
            ctx.bot.config.get('bot', 'waifu'),
            ctx.bot.session,
            for_user=ctx.author.id,
            nsfw=(ctx.channel.nsfw if isinstance(ctx.channel, discord.TextChannel) else False),
            source=source,
        )
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
                    (f'> [#{data["image_id"]}]({data["source"]})' if data['image_id'] and data['source'] else None),
                    '<:smash:1276874474628583497> **Smashers:** ' + smasher,
                    '<:pass:1276874515296813118> **Passers:** ' + passer,
                ],
                seperator='\n',
            ),
            colour=(discord.Colour.from_str(data['dominant_color']) if data['dominant_color'] else None),
        )

        embed.set_image(url=data['url'])

        return embed

    @discord.ui.button(
        emoji='<:smash:1276874474628583497>',
        style=discord.ButtonStyle.green,
    )
    async def smash(self, interaction: discord.Interaction[DeBot], _: discord.ui.Button[Self]) -> None:
        if interaction.user in self.smashers:
            interaction.channel = cast(discord.TextChannel, interaction.channel)
            try:
                await interaction.client.pool.execute(
                    """INSERT INTO WaifuFavourites VALUES ($1, $2, $3, $4)""",
                    self.current['url'],
                    interaction.user.id,
                    interaction.channel.is_nsfw(),
                    datetime.datetime.now(tz=datetime.UTC),
                )
            except UniqueViolationError:
                return await interaction.response.send_message(
                    'You have already added this waifu in your favourites list',
                    ephemeral=True,
                )
            return await interaction.response.send_message(
                f'Successfully added [#{self.current["image_id"]}](<{self.current["url"]}>) to your favourites!',
                ephemeral=True,
            )

        if interaction.user in self.passers:
            self.passers.remove(interaction.user)

        self.smashers.add(interaction.user)
        await interaction.client.pool.execute(
            """
                INSERT INTO
                    Waifus (id, smashes, nsfw, type)
                VALUES
                    ($1, 1, $2, $3)
                ON CONFLICT (id, type) DO
                UPDATE
                SET
                    smashes = Waifus.smashes + 1
            """,
            self.current['image_id'],
            self.nsfw,
            self.source,
        )
        await interaction.response.edit_message(embed=self.embed(self.current))
        return None

    @discord.ui.button(
        emoji='<:pass:1276874515296813118>',
        style=discord.ButtonStyle.red,
    )
    async def passbutton(self, interaction: discord.Interaction[DeBot], _: discord.ui.Button[Self]) -> None:
        if interaction.user in self.passers:
            return await interaction.response.defer()

        if interaction.user in self.smashers:
            self.smashers.remove(interaction.user)

        self.passers.add(interaction.user)
        await interaction.client.pool.execute(
            """
                INSERT INTO
                    Waifus (id, passes, nsfw, type)
                VALUES
                    ($1, 1, $2, $3)
                ON CONFLICT (id, type) DO
                UPDATE
                SET
                    passes = Waifus.passes + 1
                """,
            self.current['image_id'],
            self.nsfw,
            self.source,
        )
        await interaction.response.edit_message(embed=self.embed(self.current))
        return None

    @discord.ui.button(emoji='🔁', style=discord.ButtonStyle.grey)
    async def _next(self, interaction: discord.Interaction[DeBot], _: discord.ui.Button[Self]) -> None:
        self.smashers.clear()
        self.passers.clear()
        try:
            data = await self.request()
        except KeyError:
            await interaction.response.send_message('Hey! Slow down.', ephemeral=True)
        else:
            await interaction.response.edit_message(embed=self.embed(data))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.for_user:
            return True

        if (
            interaction.user.id != self.for_user
            and interaction.data
            and interaction.data.get('custom_id') == self._next.custom_id
        ):
            await interaction.response.send_message(
                'Only the command initiator can cycle through waifus in this message.',
                ephemeral=True,
            )

            return False

        return True


class WaifuView(SmashOrPass):
    async def request(self) -> Image:
        waifu = await self.session.get(
            'https://api.waifu.im/search',
            params={
                'is_nsfw': 'false' if self.nsfw is False else 'null',
                'token': self.token,
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


class WaifuViewBackup(SmashOrPass):
    async def request(self) -> Image:
        waifu = await self.session.get(f'https://api.waifu.pics/{"nsfw" if self.nsfw is True else "sfw"}/waifu')

        data = await waifu.json()

        current: Image = {
            'image_id': data['url'],
            'dominant_color': None,
            'source': data['url'],
            'url': data['url'],
        }
        self.current = current

        return self.current


class SafebooruPokemonView(SmashOrPass):
    async def request(self) -> Image:
        waifu = await self.session.get(
            'https://danbooru.donmai.us/posts/random.json',
            params={
                'tags': better_string(['solo', 'pokemon_(creature)'], seperator=' '),
                'rating': better_string(['explicit', 'questionable', 'sensitive'], seperator=',')
                if self.nsfw is True
                else 'general',
            },
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
