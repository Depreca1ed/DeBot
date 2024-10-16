from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils import BaseCog, Embed, better_string

if TYPE_CHECKING:
    from utils import DeContext


class RoleInfo(BaseCog):
    @commands.hybrid_command(name='roleinfo', help='Get information about a role', aliases=['role'])
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=True)
    @commands.guild_only()
    async def roleinfo(self, ctx: DeContext, role: discord.Role) -> discord.Message:
        embed = Embed(
            title=f"{role.name} {role.unicode_emoji if role.unicode_emoji else ''}",
            colour=role.colour,
            ctx=ctx,
        )
        embed.description = better_string(
            (
                f'- **ID:** {role.id}',
                f"- **Created:** {discord.utils.format_dt(role.created_at, 'D')} ({discord.utils.format_dt(role.created_at, 'R')})",
                (f'> `{len(role.members)}` users have this role.' if role.members else None),
            ),
            seperator='\n',
        )
        embed.set_thumbnail(url=role.icon.url if role.icon else None)
        if role.tags:
            embed.add_field(
                value=better_string(
                    (
                        ('- This is a **server booster** role' if role.is_premium_subscriber() else None),
                        ('- This role is managed by an **integration**' if role.is_integration() else None),
                        ('- This role is for an **app**' if role.is_bot_managed() else None),
                    ),
                    seperator='\n',
                ),
            )
        return await ctx.reply(embed=embed)
