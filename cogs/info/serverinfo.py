from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils import YukiEmbed

if TYPE_CHECKING:
    from bot import YukiSuou


class ServerInfo(commands.Cog):
    def __init__(self, bot: YukiSuou) -> None:
        self.bot = bot

    @commands.hybrid_command(name='serverinfo', description='Get information about the server')
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context[YukiSuou]) -> None:
        assert ctx.guild is not None
        guild = ctx.guild

        embed = YukiEmbed(description=guild.description or None, ctx=ctx)
        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)

        guild_data = [
            f"- **Owner:** {guild.owner.mention if guild.owner else f'<@{guild.owner_id}>'} (`{guild.owner_id}`)",
            f'- **ID: ** {guild.id}',
            f"- **Created:** {discord.utils.format_dt(guild.created_at, 'D')} ({discord.utils.format_dt(guild.created_at, 'R')})",
        ]
        embed.add_field(name='', value='\n'.join(guild_data), inline=False)

        valid_roles = [role.mention for role in guild.roles if role is not guild.default_role]
        valid_roles.reverse()
        emojis = [str(emoji) for emoji in guild.emojis]
        statistic_data = [
            f'- **Members:** `{guild.member_count}`',
            f'- **Channels:** `{len(guild.channels)}`',
            (
                f"- **Roles: ** {', '.join(valid_roles) if len(valid_roles) <= 3 else ', '.join(valid_roles[:3]) + f' + {len(valid_roles)-3} roles'}"  # noqa: PLR2004
                if valid_roles
                else None
            ),
            (
                f"- **Emojis: ** {' '.join(emojis) if len(emojis) <= 3 else ' '.join(emojis[:3]) + f' + {len(emojis)-3} emojis'} (`{len(guild.emojis)}/{guild.emoji_limit}`)"  # noqa: PLR2004
                if valid_roles
                else None
            ),
        ]
        embed.add_field(name='Statistics', value='\n'.join([data for data in statistic_data if data]), inline=False)

        if guild.premium_subscription_count:
            boosters = [
                str(a.mention)
                for a in sorted(
                    guild.premium_subscribers,
                    key=lambda m: m.premium_since if m.premium_since else (m.joined_at or m.created_at),
                )
            ]

            booster_listing = [
                f'> **{guild.name}** has `{guild.premium_subscription_count}` boosts and is at **Level `{guild.premium_tier}`**',
                f'- **Booster Role: ** {guild.premium_subscriber_role.mention}' if guild.premium_subscriber_role else None,
                (
                    f"- **Boosters: ** {', '.join(boosters) if len(boosters) <= 5 else ', '.join(boosters[:5]) + f' + {len(boosters)-5} boosters'}"  # noqa: PLR2004
                    if valid_roles
                    else None
                ),
            ]
            embed.add_field(name='Nitro Boosts', value='\n'.join([data for data in booster_listing if data]))

        banner_or_splash = guild.banner or guild.splash
        embed.set_image(url=banner_or_splash.url if banner_or_splash else None)

        await ctx.send(embed=embed)


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(ServerInfo(bot))
