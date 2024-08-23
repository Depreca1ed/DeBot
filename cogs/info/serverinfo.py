from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils import YukiEmbed, better_string

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

        embed.add_field(
            value=better_string(
                [
                    f"- **Owner:** {guild.owner.mention if guild.owner else f'<@{guild.owner_id}>'} (`{guild.owner_id}`)",
                    f'- **ID: ** {guild.id}',
                    f"- **Created:** {discord.utils.format_dt(guild.created_at, 'D')} ({discord.utils.format_dt(guild.created_at, 'R')})",
                ],
                seperator='\n',
            ),
        )

        valid_roles = [role.mention for role in guild.roles if role is not guild.default_role]
        valid_roles.reverse()
        emojis = [str(emoji) for emoji in guild.emojis]
        embed.add_field(
            name='Statistics',
            value=better_string(
                [
                    f'- **Members:** `{guild.member_count}`',
                    f'- **Channels:** `{len(guild.channels)}`',
                    better_string(
                        [
                            f"- **Roles: ** {', '.join(valid_roles) if len(valid_roles) <= 3 else ', '.join(valid_roles[:3]) + f' + {len(valid_roles)-3} roles'}",  # noqa: PLR2004
                            f"- **Emojis: ** {' '.join(emojis) if len(emojis) <= 3 else ' '.join(emojis[:3]) + f' + {len(emojis)-3} emojis'} (`{len(guild.emojis)}/{guild.emoji_limit}`)",  # noqa: PLR2004
                        ],
                        seperator='\n',
                    )
                    if valid_roles
                    else None,
                ],
                seperator='\n',
            ),
        )

        if guild.premium_subscription_count:
            boosters = [
                str(a.mention)
                for a in sorted(
                    guild.premium_subscribers,
                    key=lambda m: m.premium_since if m.premium_since else (m.joined_at or m.created_at),
                )
            ]

            embed.add_field(
                name='Nitro Boosts',
                value=better_string(
                    [
                        f'> **{guild.name}** has `{guild.premium_subscription_count}` boosts and is at **Level `{guild.premium_tier}`**',
                        f'- **Booster Role: ** {guild.premium_subscriber_role.mention}'
                        if guild.premium_subscriber_role
                        else None,
                        (
                            f"- **Boosters: ** {', '.join(boosters) if len(boosters) <= 5 else ', '.join(boosters[:5]) + f' + {len(boosters)-5} boosters'}"  # noqa: PLR2004
                            if valid_roles
                            else None
                        ),
                    ],
                    seperator='\n',
                ),
            )

        banner_or_splash = guild.banner or guild.splash
        embed.set_image(url=banner_or_splash.url if banner_or_splash else None)

        await ctx.send(embed=embed)


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(ServerInfo(bot))
