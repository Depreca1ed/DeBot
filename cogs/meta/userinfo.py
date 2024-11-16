from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils import ActivityHandler, BaseCog, DeContext, Embed, better_string


class Userinfo(BaseCog):
    @commands.hybrid_command(name='whois', help='Get information about a user', aliases=['userinfo', 'who'])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def whois(
        self,
        ctx: DeContext,
        user: discord.Member | discord.User | None,
    ) -> None:
        user = user or ctx.author
        embed = Embed(
            title=str(user),
            colour=user.colour if user.colour != discord.Colour.default() else None,
            ctx=ctx,
        )
        name = (
            f'{user.global_name or user.name}' + ' ' + f'({user.nick} in {user.guild.name})'
            if isinstance(user, discord.Member) and user.nick and user.guild.name
            else ''
        )
        embed.set_author(
            name=name,
            icon_url=user.avatar.url if user.avatar else user.default_avatar.url,
        )

        basic_user_listing = better_string(
            [
                f'- **ID:** {user.id}',
                f"- **Created:** {discord.utils.format_dt(user.created_at, 'D')} ({discord.utils.format_dt(user.created_at, 'R')})",  # noqa: E501 # Im gonna kill myself
            ],
            seperator='\n',
        )
        base_shown_count = 5
        acknoledgements: list[str] = []
        if isinstance(user, discord.Member):
            valid_roles = [role.mention for role in user.roles if role is not user.guild.default_role]
            valid_roles.reverse()

            member_listing = better_string(
                [
                    (
                        f"- **Joined:** {discord.utils.format_dt(user.joined_at, 'D')} ({discord.utils.format_dt(user.joined_at, 'R')})"  # noqa: E501
                        if user.joined_at
                        else None
                    ),
                    (
                        f"- **Roles: ** {', '.join(valid_roles) if len(valid_roles) <= base_shown_count else ', '.join(valid_roles[:5]) + f' + {len(valid_roles)-base_shown_count} roles'}"  # noqa: E501
                        if valid_roles
                        else None
                    ),
                ],
                seperator='\n',
            )
            basic_user_listing += f'\n{member_listing}'
            for message in ActivityHandler.status_message_generator(user.activities):
                if len(embed.fields) <= base_shown_count:
                    embed.add_field(value=message)
            if [r for r in user.roles if r] and [
                perm
                for perm in user.guild_permissions
                if perm in [subperm for subperm in discord.Permissions.elevated() if subperm[1] is True] and perm[1] is True
            ]:
                acknoledgements.append('Server Staff')
        embed.add_field(value=basic_user_listing)
        if acknoledgements:
            embed.add_field(name='Acknowledgements', value='\n'.join(acknoledgements), inline=False)

        embed.set_thumbnail(url=user.display_avatar.url)

        await ctx.send(embed=embed)
