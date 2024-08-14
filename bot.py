import configparser
import datetime
import functools
import json
import logging
from itertools import product
from pathlib import Path
from pkgutil import iter_modules
from typing import Any, ClassVar, Self

import aiohttp
import asqlite
import discord
import jishaku
import mystbin
from discord.ext import commands

from utils.Error import PrefixAlreadyPresent, PrefixNotInitialised, PrefixNotPresent

log: logging.Logger = logging.getLogger(__name__)

jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True
jishaku.Flags.USE_ANSI_ALWAYS = True
jishaku.Flags.NO_UNDERSCORE = True

BASE_PREFIX = "Yuki"


class YukiSuou(commands.Bot):
    prefix: ClassVar[list[str]] = [
        "".join(capitalization) for capitalization in product(*zip(BASE_PREFIX.lower(), BASE_PREFIX.upper()))
    ]
    colour = color = 0xFFFFFF
    pool: asqlite.Pool
    session: aiohttp.ClientSession

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        intents: discord.Intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.get_prefix,  # pyright: ignore[reportArgumentType]
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
        self.prefixes: dict[int, list[str]] = {}

    async def get_prefix(self, message: discord.Message) -> list[str]:
        prefixes = self.prefix.copy()
        if message.guild is None:
            return commands.when_mentioned_or(*prefixes)(self, message)

        if self.prefixes.get(message.guild.id):
            prefixes.extend(self.prefixes[message.guild.id])
            return commands.when_mentioned_or(*prefixes)(self, message)

        async with self.pool.acquire() as conn:
            fetched_prefix: list[str] = json.loads(
                (
                    await conn.fetchone(
                        """SELECT json_group_array(prefix) AS Prefixes FROM prefixes WHERE guild = ?""",
                        (message.guild.id),
                    )
                )[0]
            )
        if fetched_prefix:
            self.prefixes[message.guild.id] = fetched_prefix
            prefixes.extend(self.prefixes[message.guild.id])

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def add_prefix(self, guild: discord.Guild, prefix: str) -> list[str]:
        if prefix in self.prefix:
            raise PrefixAlreadyPresent(f"{prefix} is an already present prefix.")
        async with self.pool.acquire() as conn:
            await conn.execute("""INSERT INTO Prefixes VALUES (?, ?)""", (guild.id, prefix))
        #TODO: IMPORTANT: Modify schema to allow multiple entries of guild and prefix but not a duplicate row.
        if not self.prefixes.get(guild.id):
            self.prefixes[guild.id] = [prefix]
            return self.prefixes[guild.id]
        self.prefixes[guild.id].append(prefix)

        return self.prefixes[guild.id]

    async def remove_prefix(self, guild: discord.Guild, prefix: str) -> list[str]:
        if not self.prefixes.get(guild.id):
            raise PrefixNotInitialised(f"Prefixes were not initialised for {guild.id}")

        elif prefix not in self.prefixes[guild.id]:
            raise PrefixNotPresent(f"{prefix} is not present in guild: {guild.id}")
        async with self.pool.acquire() as conn:
            await conn.execute("""DELETE FROM Prefixes WHERE guild = ? AND prefix = ?""", (guild.id, prefix))
        self.prefixes[guild.id].remove(prefix)
        if not self.prefixes[guild.id]:
            self.prefixes.pop(guild.id)  # NOTE: This is an excessive cleaner. Unsure if it should be present
        return self.prefixes[guild.id]

    async def get_prefix_list(self, guild: discord.Guild) -> list[str]:
        prefixes = [BASE_PREFIX]
        if self.prefixes.get(guild.id):
            prefixes.extend(self.prefixes[guild.id])

        return prefixes

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
        self.pool: asqlite.Pool = await asqlite.create_pool("database/db.db")
        async with self.pool.acquire() as db:

            with Path("schema.sql").open(encoding="utf-8") as f:
                await db.executescript(f.read())

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
        if hasattr(self, "pool"):
            await self.pool.close()
        if hasattr(self, "session"):
            await self.session.close()
        await super().close()
