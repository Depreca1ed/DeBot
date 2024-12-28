from __future__ import annotations

from typing import Literal

import discord
from discord.ext import commands

from utils import BaseCog, Embed, better_string

BOT_THRESHOLD = 80
BLACKLIST_COLOUR = discord.Colour.from_str('#ccaa88')
BOT_FARM_COLOUR = discord.Colour.from_str('#fff5e8')


def guild_embed(guild: discord.Guild, event_type: Literal['Joined', 'Left']) -> Embed:
    return Embed(
        description=better_string(
            [
                f"- **Owner:** {guild.owner.mention if guild.owner else f'<@{guild.owner_id}>'} (`{guild.owner_id}`)",
                f'- **ID: ** {guild.id}',
                f"- **Created:** {discord.utils.format_dt(guild.created_at, 'D')} ({discord.utils.format_dt(guild.created_at, 'R')})",  # noqa: E501
                f'- **Member Count:** `{guild.member_count}`',
            ],
            seperator='\n',
        ),
    ).set_author(name=f'{event_type} {guild}', icon_url=guild.icon.url if guild.icon else None)


def bot_farm_check(guild: discord.Guild) -> bool:
    bots = len([_ for _ in guild.members if _.bot is True])
    members = len(guild.members)
    return (bots / members) * 100 > BOT_THRESHOLD


class Guild(BaseCog):
    @commands.Cog.listener('on_guild_join')
    async def guild_join(self, guild: discord.Guild) -> None:
        blacklisted = bot_farm = False
        if self.bot.blacklist.is_blacklisted(guild):
            blacklisted = True
            await guild.leave()
        if bot_farm_check(guild):
            bot_farm = True

        embed = guild_embed(guild, 'Joined')
        embed.colour = (
            (BLACKLIST_COLOUR if blacklisted is True else None) or (BOT_FARM_COLOUR if bot_farm is True else None) or None
        )

        if blacklisted or bot_farm:
            embed.add_field(
                value=better_string(
                    (
                        '- This guild is blacklisted. I have left the server automatically' if blacklisted is True else None,
                        '- This guild is a bot farm' if bot_farm is True else None,
                    ),
                    seperator='\n',
                )
            )

        await self.bot.logger_webhook.send(embed=embed)

    @commands.Cog.listener('on_guild_remove')
    async def guild_leave(self, guild: discord.Guild) -> None:
        embed = guild_embed(guild, 'Left')
        await self.bot.logger_webhook.send(embed=embed)
