from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils.Embed import YukiEmbed
from utils.HelperFunctions import DefaultToUser, StatusMessageGen

if TYPE_CHECKING:
    from bot import YukiSuou

badges_to_emoji = {
    "partner": "<:discordpartner:1250444436148584494>",
    "verified_bot_developer": "<:discordbotdev:1250444367315861674>",
    "hypesquad_balance": "<:hypesquadbalance:1250444397997330432>",
    "hypesquad_bravery": "<:hypesquadbravery:1250444393354231888>",
    "hypesquad_brilliance": "<:hypesquadbrilliance:1250444388111355904>",
    "bug_hunter": "<:discordbughunter1:1250444423225937960>",
    "hypesquad": "<:hypesquadevents:1250444402661396581>",
    "early_supporter": "<:discordearlysupporter:1250444410517323856>",
    "bug_hunter_level_2": "<:discordbughunter2:1250444418905800805> ",
    "staff": "<:discordstaff:1250444441727008850>",
    "discord_certified_moderator": "<:olddiscordmod:1250444414476750994>",
    "active_developer": "<:activedeveloper:1250444432042491957>",
}  # Credits to https://github.com/Rapptz/RoboDanny/blob/cf7e4ec88882175eb18b1152ea60755d08c05de2/cogs/meta.py#L490


class Userinfo(commands.Cog):
    def __init__(self, bot: YukiSuou) -> None:
        self.bot = bot

    @commands.hybrid_command(name="whois", description="Get information about a user", aliases=["userinfo", "who"])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def whois(
        self,
        ctx: commands.Context[YukiSuou],
        user: discord.Member | discord.User = commands.parameter(default=DefaultToUser),
    ) -> None:
        embed = YukiEmbed.default(ctx, title=str(user), colour=user.colour)

        embed.set_author(
            name=f"{user.global_name or user.name} {f'({user.nick} in {user.guild.name})' if isinstance(user, discord.Member) and user.nick and user.guild.name else ''}",
            icon_url=user.avatar.url if user.avatar else user.default_avatar.url,
        )
        set_flags = {
            flag for flag, value in user.public_flags if value
        }  # Credits to https://github.com/Rapptz/RoboDanny/blob/cf7e4ec88882175eb18b1152ea60755d08c05de2/cogs/meta.py#L513

        embed.description = "".join(
            badge for badge in [badges_to_emoji[flag] for flag in (set_flags & badges_to_emoji.keys())]
        )

        basic_user_listing = [
            f"- **ID:** {user.id}",
            f"- **Created:** {discord.utils.format_dt(user.created_at, 'D')} ({discord.utils.format_dt(user.created_at, 'R')})",
        ]

        acknoledgements: list[str] = []
        if isinstance(user, discord.Member):
            valid_roles = [role.mention for role in user.roles if role is not user.guild.default_role]
            valid_roles.reverse()
            member_listing = [
                obj
                for obj in [
                    (
                        (
                            f"- **Joined:** {discord.utils.format_dt(user.joined_at, 'D')} ({discord.utils.format_dt(user.joined_at, 'R')})"
                            if user.joined_at
                            else None
                        )
                    ),
                    (
                        f"- **Roles: ** {', '.join(valid_roles) if len(valid_roles) <= 5 else ', '.join(valid_roles[:5]) + f' + {len(valid_roles)-5} roles'}"
                        if valid_roles
                        else None
                    ),
                ]
                if obj
            ]
            basic_user_listing.extend(member_listing)
            if (
                (status := StatusMessageGen(user))
                and status
                and len(embed.fields) <= 5
                and (user.activity or user.activities)
            ):
                for that_string in status:
                    embed.add_field(name="", value=that_string, inline=False)
            if [r for r in user.roles if r] and [
                perm
                for perm in user.guild_permissions
                if perm in [subperm for subperm in discord.Permissions.elevated() if subperm[1] is True] and perm[1] is True
            ]:  # https://github.com/Rapptz/discord.py/blob/c055fd32bbe5c68b144a7ac938b911035eb6d3e1/discord/member.py#L724 causes the bot to check a false property therefore im manually making my own check
                acknoledgements.append("<:discordstaff:1250444441727008850> Server Staff")
        embed.add_field(name=" ", value="\n".join(basic_user_listing), inline=False)
        if acknoledgements:
            embed.add_field(name="Acknowledgements", value="\n".join(acknoledgements), inline=False)

        embed.set_thumbnail(url=user.display_avatar.url)

        await ctx.send(embed=embed)


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(Userinfo(bot))
