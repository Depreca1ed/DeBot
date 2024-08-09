import configparser
import datetime
import functools
import json
import logging
import os
from pathlib import Path
from pkgutil import iter_modules
from typing import Any, ClassVar, Self

import aiohttp
import asqlite
import discord
import mystbin
from discord.ext import commands, tasks

log: logging.Logger = logging.getLogger(__name__)


class Elysian(commands.Bot):
    prefix: ClassVar[list[str]] = ["e!", "E!"]
    colour = color = 0xFFFFFF

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        intents: discord.Intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.get_prefix,  # type: ignore
            description="Custom Bot for Wordism server.",
            case_insensitive=True,
            strip_after_prefix=True,
            intents=intents,
            max_messages=5000,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True),
            owner_ids=[688293803613880334],
            *args,
            **kwargs,
        )

        self.token = str(self.config.get("TOKENS", "bot"))
        self.session = aiohttp.ClientSession()
        self.mystbin = mystbin.Client()
        self.load_time = datetime.datetime.now(datetime.UTC)
        self.prefixless_check = True
        self.prefixes: dict[int, list[str]] = {}

    async def blacklistcheck(self, ctx: commands.Context[Self]) -> bool:
        if ctx.author.id not in self.blacklistedusers:
            return True
        if isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.channel.send(
                f"Hey {ctx.author!s}! You are currently blacklisted from using the bot. You will not be able to run my commands in any servers or DMs"
            )
        return False

    async def get_prefix(self, message: discord.Message) -> list[str] | str:
        if self.owner_ids and message.author.id in self.owner_ids and self.prefixless_check is True:
            return [""]
        prefixes = self.prefix.copy()
        if message.guild and message.guild.id in self.prefixes:
            prefixes.extend(self.prefixes[message.guild.id])
        return commands.when_mentioned_or(*prefixes)(self, message)

    @property
    def config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read("config/config.ini")
        return config

    async def setup_hook(self) -> None:
        log.info("Setting up bot")

        self.pool = await asqlite.create_pool("database/db.db")
        async with self.pool.acquire() as db:
            with Path("schema.sql").open(encoding="utf-8") as f:
                await db.executescript(f.read())

            blacklisted_users = await db.fetchall("SELECT * FROM blacklists WHERE type = 'user'")
            blacklisted_guilds = await db.fetchall("SELECT * FROM blacklists WHERE type = 'guild'")
            prefixes_cached = await db.fetchall(
                "SELECT guild, json_group_array(prefix) AS prefixes FROM prefixes GROUP BY guild"
            )
            snipe_guilds = await db.fetchall("SELECT id FROM Features WHERE type = 'Snipe'")
            message_logger_guilds = await db.fetchall("SELECT id FROM Features WHERE type = 'Messages'")
        self.prefixes = {guild: json.loads(prefix) for guild, prefix in prefixes_cached}
        self.blacklistedusers: list[int] = [blacklist[0] for blacklist in blacklisted_users]
        self.blacklistedguilds: list[int] = [blacklist[0] for blacklist in blacklisted_guilds]
        self.snipe_guilds: list[int] = [snipe_guild[0] for snipe_guild in snipe_guilds]
        self.messages_logger_guilds: list[int] = [message_logger_guild[0] for message_logger_guild in message_logger_guilds]
        log.info("Database cache filled")

        for cog in [m.name for m in iter_modules(["cogs"], prefix="cogs.")]:
            try:
                await self.load_extension(str(cog))
            except Exception as error:
                log.error("Ignoring exception in loading %s", cog, exc_info=error)
            else:
                log.info("%s loaded", cog)

        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
        await self.load_extension("jishaku")
        log.info("jishaku loaded")

        self.add_check(self.blacklistcheck)
        self.activitystatus.start()
        log.info("Setup complete")

    @tasks.loop(minutes=1)
    async def activitystatus(self) -> None:
        await self.change_presence(
            activity=discord.CustomActivity(name=f"Watchingg {len(self.guilds)} servers and {len(self.users)} users")
        )

    @activitystatus.before_loop
    async def beforethatloopy(self) -> None:
        await self.wait_until_ready()

    async def close(self) -> None:
        await self.pool.close()
        await self.session.close()
        await super().close()

    @functools.cached_property
    def logger_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(self.config.get("WEBHOOKS", "logger"), session=self.session, bot_token=self.token)

    @property
    def guild(self) -> discord.Guild:
        guild = self.get_guild(1262409199552430170)
        assert guild is not None
        return guild
