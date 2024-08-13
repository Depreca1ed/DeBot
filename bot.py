import configparser
import datetime
import functools
import json
import logging
from pathlib import Path
from pkgutil import iter_modules
from typing import Any, ClassVar, Self

import aiohttp
import asqlite
import discord
import jishaku
import mystbin
from discord.ext import commands

log: logging.Logger = logging.getLogger(__name__)

jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True
jishaku.Flags.USE_ANSI_ALWAYS = True
jishaku.Flags.NO_UNDERSCORE = True


class YukiSuou(commands.Bot):
    prefix: ClassVar[list[str]] = ["+", "y!"]
    colour = color = 0xFFFFFF

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        intents: discord.Intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.get_prefix_func,
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
        self.prefixes: dict[int, str] = {}

    @classmethod
    async def get_prefix_func(cls, client: Self, message: discord.Message) -> list[str] | str:
        prefixes = client.prefix.copy()
        if message.guild and message.guild.id in client.prefixes:
            prefixes.extend(client.prefixes[message.guild.id])
        return commands.when_mentioned_or(*prefixes)(client, message)

    async def blacklistcheck(self, ctx: commands.Context[Self]) -> bool:
        if ctx.author.id not in self.blacklistedusers:
            return True
        if isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.channel.send(
                f"Hey {ctx.author!s}! You are currently blacklisted from using the bot. You will not be able to run my commands in any servers or DMs"
            )
        return False

    @property
    def config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read("config/config.ini")
        return config

    async def setup_hook(self) -> None:
        self.pool = await asqlite.create_pool("database/db.db")
        async with self.pool.acquire() as db:

            with Path("schema.sql").open(encoding="utf-8") as f:
                await db.executescript(f.read())

            self.prefixes: dict[int, str] = {
                guild: json.loads(prefix)
                for guild, prefix in await db.fetchall(
                    """SELECT guild, json_group_array(prefix) AS prefixes FROM prefixes GROUP BY guild"""
                )
            }
            self.blacklistedguilds: list[int] = [
                blacklist[0] for blacklist in await db.fetchall("""SELECT * FROM blacklists WHERE type = 'guild'""")
            ]
            self.blacklistedusers = [
                blacklist[0] for blacklist in await db.fetchall("""SELECT * FROM blacklists WHERE type = 'user'""")
            ]

        cogs = [m.name for m in iter_modules(["cogs"], prefix="cogs.")]
        external_cogs = ["jishaku"]

        cogs.extend(external_cogs)

        for cog in cogs:
            try:
                await self.load_extension(str(cog))
            except commands.ExtensionError as error:
                log.error("%s \U00002717\nIgnoring exception in loading %s", cog, exc_info=error)
            else:
                log.info("%s \U00002713", cog)

        self.add_check(self.blacklistcheck)
        log.info("Setup complete")

    @functools.cached_property
    def logger_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(self.config.get("WEBHOOKS", "logger"), session=self.session, bot_token=self.token)

    @property
    def guild(self) -> discord.Guild:
        guild = self.get_guild(1262409199552430170)
        assert guild is not None
        return guild

    @property
    def user(self) -> discord.ClientUser:
        user = super().user
        assert user is not None
        return user

    async def close(self) -> None:
        await self.pool.close()
        await self.session.close()
        await super().close()
