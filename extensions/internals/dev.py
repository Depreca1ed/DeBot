from __future__ import annotations

import discord
import datetime
from discord.ext import commands

from utils import AlreadyBlacklistedError, BaseCog, Context, better_string


class Developer(BaseCog):
    @commands.command(name='reload', aliases=['re'], hidden=True)
    async def reload_cogs(self, ctx: Context) -> None:
        exts = self.bot.initial_extensions
        messages: list[str] = []

        for ext in exts:
            try:
                await self.bot.reload_extension(str(cog))
            except commands.ExtensionError as error:
                messages.append(f'Failed to reload {cog}\n```py{error}```')
            else:
                messages.append(f'Reloaded {cog}')

        await ctx.send(content=better_string(messages, seperator='\n'))

    @commands.group(
        name='blacklist',
        aliases=['bl'],
        invoke_without_command=True,
        help='The command which handles bot blacklists',
    )
    async def blacklist_cmd(self, ctx: Context) -> None:
        bl = self.bot.blacklist

        bl_guild_count = len([entry for entry in bl.blacklist_cache if bl.blacklist_cache[entry].blacklist_type == 'guild'])
        bl_user_count = len([entry for entry in bl.blacklist_cache if bl.blacklist_cache[entry].blacklist_type == 'user'])

        content = f'Currently, `{bl_guild_count}` servers and `{bl_user_count}` users are blacklisted.'
        await ctx.reply(content=content)

    @blacklist_cmd.command(name='add', help='Add a user to the blacklist')
    async def blacklist_user_add(
        self,
        ctx: Context,
        user: discord.User | discord.Member,
        until: str | None,
        *,
        reason: str = 'No reason provided',
    ):
        bl_until = None
        if until:
            suffixes = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400,
                'mo': 2592000,
                'y': 2592000 * 12,
            }

            if until[-1:] not in suffixes:
                return await ctx.reply(f"{ctx.author.mention}, i can't understand the time you provided.")
            parsed = suffixes[until[-1:]]
            c = int(until[:-1]) if until[-2:] != 'mo' else int(until[-2:])
            final = c * parsed
            bl_until = datetime.datetime.now() + datetime.timedelta(seconds=final)

        try:
            await self.bot.blacklist.add(user, lasts_until=bl_until, reason=reason)

        except AlreadyBlacklistedError as err:
            content = str(err)
            await ctx.reply(content)

        await ctx.message.add_reaction(self.bot.bot_emojis['green_tick'])
        return None

    @blacklist_cmd.command(name='remove', help='Remove a user from blacklist')
    async def blacklist_user_remove(self, ctx: Context, user: discord.User | discord.Member) -> None:
        try:
            await self.bot.blacklist.remove(user)

        except AlreadyBlacklistedError as err:
            content = str(err)
            await ctx.reply(content)

        await ctx.message.add_reaction(self.bot.bot_emojis['green_tick'])
