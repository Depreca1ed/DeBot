import asyncio
import contextlib
import json
from typing import Any, Never

import discord
import mystbin
from discord.ext import commands

from bot import Elysian
from utils.Embed import ElyEmbed
from utils.Pagination import ElyPagination


class Dev(commands.Cog):
    def __init__(self, bot: Elysian) -> None:
        self.bot = bot

    @commands.group(
        name="dev",
        description="Developer commands",
        invoke_without_command=True,
        hidden=True,
    )
    @commands.is_owner()
    async def dev(self, ctx: commands.Context[Any]) -> None:
        await ctx.send_help(ctx.command)

    @dev.command(name="beta", description="Yes")
    @commands.is_owner()
    async def beta(self, ctx: commands.Context[Any]) -> Never:
        raise commands.CommandError("I love women")

    @dev.command(name="say", description="Say things")
    @commands.is_owner()
    async def say(self, ctx: commands.Context[Any], *, message: str) -> discord.Message | discord.PartialMessage:
        with contextlib.suppress(discord.HTTPException):
            await ctx.message.delete()
        return (
            await ctx.message.reference.resolved.reply(content=message)
            if ctx.message.reference
            and not isinstance(ctx.message.reference.resolved, discord.DeletedReferencedMessage)
            and ctx.message.reference.resolved is not None
            else await ctx.send(content=message)
        )

    @dev.command(name="pull", description="Pull things")
    @commands.is_owner()
    async def pull(self, ctx: commands.Context[Any]) -> None:
        result = await self.shell("git pull")
        output = "\n".join(i.strip() for i in result)
        embed = ElyEmbed.default(ctx, title="Pulling from source", description="```ansi\n" + output + "```")
        msg = await ctx.reply(embed=embed)
        reloads: list[str] = []
        cogs = list(self.bot.cogs)
        cogs.remove("Jishaku")
        successfuls = 0
        failures = 0
        for cog in cogs:
            try:
                await ctx.bot.reload_extension("cogs." + cog)
            except Exception as err:
                reloads.append(f"<:redTick:1237048136527249510> Failed to reload **{cog}**.py\nError: ```py\n{err!s}```")
                failures = failures + 1
            else:
                reloads.append(f"<:greenTick:1237048095699636245> Successfully reloaded **{cog}.py**")
                successfuls = successfuls + 1
        embed.add_field(
            name=f"Successfully reloaded [{successfuls}/{len(ctx.bot.cogs)-1}] files with {failures} failures",
            value=str("\n".join(reloads)),
        )
        await msg.edit(embed=embed)

    async def shell(self, code: str, wait: bool = True) -> tuple[str, ...]:
        proc = await asyncio.subprocess.create_subprocess_shell(
            code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        if wait:
            await proc.wait()
        return tuple(i.decode() for i in await proc.communicate())

    @dev.command(name="del", description="Delete things")
    @commands.is_owner()
    async def dele(self, ctx: commands.Context[Any]) -> None | discord.Message:
        with contextlib.suppress(discord.HTTPException):
            return (
                await ctx.message.reference.resolved.delete()
                if ctx.message.reference
                and not isinstance(ctx.message.reference.resolved, discord.DeletedReferencedMessage)
                and ctx.message.reference.resolved is not None
                else await ctx.reply("You did not reply to a deletable message", delete_after=15.0)
            )

    @dev.command("prefixless", description="Mf boutta get or unget prefix")
    @commands.is_owner()
    async def prefixless(self, ctx: commands.Context[Any]) -> None:
        self.bot.prefixless_check = not self.bot.prefixless_check is True
        with contextlib.suppress(discord.HTTPException):
            await ctx.message.add_reaction("<:greenTick:1237048095699636245>")

    @dev.command(description="Search for emojis with name")
    @commands.guild_only()
    @commands.is_owner()
    async def emojisearch(self, ctx: commands.Context[Any], name: str) -> discord.Message | None:
        emojis = [emoji for emoji in ctx.bot.emojis if name in emoji.name]
        if not emojis:
            return await ctx.reply("Sorry, there are no emojis with that name that i can see.")
        embed = ElyEmbed.default(
            ctx,
            title=f"Emojis with the name {name}",
            description=str("\n".join([f"{emoji!s} `:` `{emoji}`" for emoji in emojis])),
        )
        await ctx.reply(embed=embed)

    @dev.group(
        name="bl",
        description="Blacklist commands",
        invoke_without_command=True,
        hidden=True,
    )
    @commands.is_owner()
    async def bl(self, ctx: commands.Context[Any]) -> Any:
        return await ctx.send_help(ctx.command)

    @bl.command(name="add", description="A motherfucker is about to be blacklisted")
    @commands.is_owner()
    async def bl_add(self, ctx: commands.Context[Any], user: discord.User) -> discord.Message:
        async with self.bot.pool.acquire() as db:
            async with db.execute("SELECT * FROM blacklists WHERE id = ? AND type = ?", (user.id, "user")) as cursor:
                already_blacklisted = await cursor.fetchone()

            if already_blacklisted:
                return await ctx.reply(f"{user} is already blacklisted")

            # Add user to the blacklist
            await db.execute("INSERT INTO blacklists (id, type) VALUES (?, ?)", (user.id, "user"))
            await db.commit()

        ctx.bot.blacklistedusers.append(user.id)
        return await ctx.reply(f"Blacklisted `{user}`")

    @bl.command(name="remove", description="A motherfucker is about to be unblacklisted")
    @commands.is_owner()
    async def bl_remove(self, ctx: commands.Context[Any], user: discord.User) -> discord.Message:
        async with self.bot.pool.acquire() as db:
            async with db.execute("SELECT * FROM blacklists WHERE id = ? AND type = ?", (user.id, "user")) as cursor:
                already_blacklisted = await cursor.fetchone()

            if not already_blacklisted:
                return await ctx.reply(f"{user} is not already blacklisted")

            # Remove user from the blacklist
            await db.execute("DELETE FROM blacklists WHERE id = ? AND type = ?", (user.id, "user"))
            await db.commit()

        ctx.bot.blacklistedusers.remove(user.id)
        return await ctx.reply(f"Unblacklisted `{user}`")

    @dev.group(
        name="gbl",
        description="Guild Blacklist commands",
        invoke_without_command=True,
        hidden=True,
    )
    @commands.is_owner()
    async def gbl(self, ctx: commands.Context[Any]) -> Any:
        return await ctx.send_help(ctx.command)

    @gbl.command(name="add", description="A guild is about to be blacklisted")
    @commands.is_owner()
    async def gbl_add(self, ctx: commands.Context[Any], guild: discord.Guild) -> discord.Message | None:
        async with self.bot.pool.acquire() as db:
            async with db.execute("SELECT * FROM blacklists WHERE id = ? AND type = ?", (guild.id, "guild")) as cursor:
                already_blacklisted = await cursor.fetchone()

            if already_blacklisted:
                return await ctx.reply(f"{guild.name} is already blacklisted")

            # Add user to the blacklist
            await db.execute("INSERT INTO blacklists (id, type) VALUES (?, ?)", (guild.id, "guild"))
            await db.commit()

            ctx.bot.blacklistedguilds.append(guild.id)
            await ctx.reply(f"Blacklisted `{guild.name}`")
            return await guild.leave()

    @gbl.command(name="remove", description="A motherfucker is about to be unblacklisted")
    @commands.is_owner()
    async def gbl_remove(self, ctx: commands.Context[Any], guild: int) -> discord.Message:
        async with self.bot.pool.acquire() as db:
            async with db.execute("SELECT * FROM blacklists WHERE id = ? AND type = ?", (guild, "guild")) as cursor:
                already_blacklisted = await cursor.fetchone()

            if not already_blacklisted:
                return await ctx.reply(f"{guild} is not already blacklisted")

            # Remove guild from the blacklist
            await db.execute("DELETE FROM blacklists WHERE id = ? AND type = ?", (guild, "guild"))
            await db.commit()

            ctx.bot.blacklistedguilds.remove(guild)
            return await ctx.reply(f"Unblacklisted `{guild}`")

    @dev.group(name="err", description="Error commands", invoke_without_command=True)
    async def error_base(self, ctx: commands.Context[Elysian]) -> None:
        await ctx.send_help(ctx.command)

    @error_base.command(
        name="show",
        description="Show details about an error. This basically shows the embed similar to what is shown in the logs",
    )
    async def error_show(self, ctx: commands.Context[Elysian]) -> discord.Message | None:
        async with self.bot.pool.acquire() as conn:
            data = await conn.fetchall("SELECT * FROM errorlogs")
        if not data:
            return await ctx.send("No currently registered errors at all in the database.")

        error_embeds: list[discord.Embed] = []

        for error in data:
            if len(error[3]) >= 1990:
                error_link = await self.bot.mystbin.create_paste(files=[mystbin.File(filename="error.py", content=error[3])])

                post_message = f"Error message was too long to be shown in this embed. \n- [Link to Error]({error_link})"
            else:
                post_message = f"```py\n{error[3]}```"

            extras = [
                f"- **Command -** {error[1]}",
                f"- **Invoked as -** {error[4]}",
                f"- **Fixed - {error[5]}**",
                f"- **Short error**\n```py\n{error[2]}```",
            ]
            error_embeds.append(
                ElyEmbed.default(
                    ctx, title=f"Error #{error[0]}", description=post_message, color=0xFF0000 if not error[5] else 0x00FF00
                ).add_field(name="Extra", value="\n".join(extras))
            )
        view = ElyPagination(error_embeds, ctx, has_timeout=True)
        message = await ctx.send(embed=error_embeds[0], view=view)
        view.message = message

    async def _basic_cleanup_strategy(self, ctx: commands.Context[Elysian], search: int) -> dict[str, int]:
        count = 0
        async for msg in ctx.history(limit=search, before=ctx.message):
            if (
                msg.author == ctx.me and not (msg.mentions or msg.role_mentions)
                if self.bot.owner_ids and msg.author.id not in self.bot.owner_ids
                else False
            ):
                await msg.delete()
                count += 1
        return {"Bot": count}

    @dev.command()
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    @commands.is_owner()
    async def cleanup(self, ctx: commands.Context[Elysian], search: int = 100) -> None:
        """Cleans up the bot's messages from the channel.

        If a search number is specified, it searches that many messages to delete.
        If the bot has Manage Messages permissions then it will try to delete
        messages that look like they invoked the bot as well.

        After the cleanup is completed, the bot will send you a message with
        which people got their messages deleted and their count. This is useful
        to see which users are spammers.

        Members with Manage Messages can search up to 1000 messages.
        Members without can search up to 25 messages.
        """

        strategy = self._basic_cleanup_strategy
        search = min(max(2, search), 25)
        spammers = await strategy(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append("")
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f"- **{author}**: {count}" for author, count in spammers)

        await ctx.send("\n".join(messages), delete_after=10)

    @dev.command()
    @commands.is_owner()
    async def cachesync(self, ctx: commands.Context[Elysian]) -> None:
        async with self.bot.pool.acquire() as db:
            blacklisted_users = await db.fetchall("SELECT * FROM blacklists WHERE type = 'user'")
            blacklisted_guilds = await db.fetchall("SELECT * FROM blacklists WHERE type = 'guild'")
            prefixes_cached = await db.fetchall(
                "SELECT guild, json_group_array(prefix) AS prefixes FROM prefixes GROUP BY guild"
            )
            snipe_guilds = await db.fetchall("SELECT id FROM Features WHERE type = 'Snipe'")
            message_logger_guilds = await db.fetchall("SELECT id FROM Features WHERE type = 'Messages'")
        self.bot.prefixes = {guild: json.loads(prefix) for guild, prefix in prefixes_cached}
        self.bot.blacklistedusers = [blacklist[0] for blacklist in blacklisted_users]
        self.bot.blacklistedguilds = [blacklist[0] for blacklist in blacklisted_guilds]
        self.bot.snipe_guilds = [snipe_guild[0] for snipe_guild in snipe_guilds]
        self.bot.messages_logger_guilds = [message_logger_guild[0] for message_logger_guild in message_logger_guilds]
        with contextlib.suppress(discord.HTTPException):
            await ctx.message.add_reaction("<:greenTick:1237048095699636245>")


async def setup(bot: Elysian) -> None:
    await bot.add_cog(Dev(bot))
