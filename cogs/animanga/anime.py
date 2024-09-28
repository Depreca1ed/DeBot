from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
import humanize
import datetime
import discord
from discord import app_commands
from discord.ext import commands

from utils import BaseCog, Embed, better_string

if TYPE_CHECKING:
    from utils import LagContext

BASIC_QUERY = """
query ($search: String, $type: MediaType) {
    Media(search: $search, type: $type, sort: POPULARITY_DESC) {
        id
        title {
            romaji
            english
            native
        }
        description(asHtml: false)
        format
        siteUrl
        episodes
        duration
        status
        chapters
        volumes
        genres
        season
        seasonYear
        meanScore
        format
        coverImage {
            extraLarge
            color
        }
    }
}
"""

bruh = re.compile(r'</?\w+/?>')


class Anime(BaseCog):
    @commands.command(name='anime')
    @commands.is_owner()
    async def anime(self, ctx: LagContext, anime: str):
        resp = await self.bot.session.post(
            'https://graphql.anilist.co/',
            json={
                'query': BASIC_QUERY,
                'variables': {
                    'search': anime,
                    'type': 'ANIME',
                },
            },
        )
        data = (await resp.json())['data']['Media']
        embed = Embed(title=f"{data['title']['english']} ({data['format']})", description=bruh.sub('', data['description']))
        embed.add_field(
            value=better_string(
                (
                    f'- **Episodes:** {data["episodes"]} ({humanize.naturaldelta(datetime.timedelta(minutes=data["episodes"]*data["duration"]))})',
                ),
                seperator='\n',
            ),
        )
        await ctx.reply(embed=embed)
