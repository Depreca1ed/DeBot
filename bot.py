from __future__ import annotations

import configparser
import datetime
import functools
import logging
from itertools import product
from pathlib import Path
from pkgutil import iter_modules
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self, overload

import aiohttp
import asyncpg
import discord
import jishaku
import mystbin
from discord.ext import commands

from utils import (
    BASE_PREFIX,
    DESCRIPTION,
    OWNERS_ID,
    THEME_COLOUR,
    Blacklist,
    DeContext,
    PrefixAlreadyPresentError,
    PrefixNotInitialisedError,
    PrefixNotPresentError,
    UnderMaintenanceError,
)

if TYPE_CHECKING:
    from discord.ext.commands._types import ContextT  # pyright: ignore[reportMissingTypeStubs]


__all__ = ('DeBot',)

log: logging.Logger = logging.getLogger(__name__)

jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True
jishaku.Flags.NO_UNDERSCORE = True


EXTERNAL_COGS: list[str] = ['jishaku']


class DeBot(commands.Bot):
    prefix: ClassVar[list[str]] = [
        ''.join(capitalization) for capitalization in product(*zip(BASE_PREFIX.lower(), BASE_PREFIX.upper(), strict=False))
    ]
    colour: discord.Colour = THEME_COLOUR
    session: aiohttp.ClientSession
    if TYPE_CHECKING:
        pool: asyncpg.Pool[asyncpg.Record]
    mystbin_cli: mystbin.Client
    load_time: datetime.datetime
    prefixes: dict[int, list[str]]
    blacklist: Blacklist
    maintenance: bool
    appinfo: discord.AppInfo
    log = log

    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.all()
        super().__init__(
            description=DESCRIPTION,
            command_prefix=self.get_prefix,  # pyright: ignore[reportArgumentType]
            case_insensitive=True,
            strip_after_prefix=True,
            intents=intents,
            max_messages=5000,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True),
        )
        self.token = str(self.config.get('bot', 'token'))
        self.session = aiohttp.ClientSession()
        self.mystbin_cli = mystbin.Client()
        self.load_time = datetime.datetime.now(tz=datetime.UTC)
        self.prefixes: dict[int, list[str]] = {}
        self.blacklist = Blacklist(self)
        self.maintenance = False
        self.check_once(self.check_maintenance)

    @discord.utils.copy_doc(commands.Bot.get_prefix)
    async def get_prefix(self, message: discord.Message) -> list[str]:
        prefixes = self.prefix.copy()
        if message.guild is None:
            return commands.when_mentioned_or(*prefixes)(self, message)

        if self.prefixes.get(message.guild.id):
            prefixes.extend(self.prefixes[message.guild.id])
            return commands.when_mentioned_or(*prefixes)(self, message)

        fetched_prefix: list[str] = await self.pool.fetchval(
            """SELECT array_agg(prefix) FROM prefixes WHERE guild = $1""",
            (message.guild.id),
        )
        if fetched_prefix:
            self.prefixes[message.guild.id] = fetched_prefix
            prefixes.extend(self.prefixes[message.guild.id])

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def add_prefix(self, guild: discord.Guild, prefix: str) -> list[str]:
        if prefix in self.prefix:
            raise PrefixAlreadyPresentError(prefix)

        await self.pool.execute("""INSERT INTO Prefixes VALUES ($1, $2)""", guild.id, prefix)
        if not self.prefixes.get(guild.id):
            self.prefixes[guild.id] = [prefix]
            return self.prefixes[guild.id]
        self.prefixes[guild.id].append(prefix)

        return self.prefixes[guild.id]

    async def remove_prefix(self, guild: discord.Guild, prefix: str) -> list[str] | None:
        if not self.prefixes.get(guild.id):
            raise PrefixNotInitialisedError(guild)

        if prefix not in self.prefixes[guild.id]:
            raise PrefixNotPresentError(prefix, guild)

        await self.pool.execute(
            """DELETE FROM Prefixes WHERE guild = $1 AND prefix = $2""",
            guild.id,
            prefix,
        )
        self.prefixes[guild.id].remove(prefix)
        if not self.prefixes[guild.id]:
            self.prefixes.pop(guild.id)
            return None
        return self.prefixes[guild.id]

    async def clear_prefix(self, guild: discord.Guild) -> None:
        if not self.prefixes.get(guild.id):
            raise PrefixNotInitialisedError(guild)

        await self.pool.execute("""DELETE FROM Prefixes WHERE guild = $1""", guild.id)

        self.prefixes.pop(guild.id)

    async def check_maintenance(self, ctx: commands.Context[Self]) -> Literal[True]:
        if self.maintenance is True and not await self.is_owner(ctx.author):
            raise UnderMaintenanceError
        return True

    async def setup_hook(self) -> None:
        credentials: dict[str, Any] = {
            'user': str(self.config.get('database', 'user')),
            'password': str(self.config.get('database', 'password')),
            'database': str(self.config.get('database', 'database')),
            'host': str(self.config.get('database', 'host')),
            'port': str(self.config.get('database', 'port')),
        }
        pool: asyncpg.Pool[asyncpg.Record] | None = await asyncpg.create_pool(**credentials)
        if not pool or (pool and pool.is_closing()):
            msg = 'Pool is closed'
            raise RuntimeError(msg)
        self.pool = pool

        with Path('schema.sql').open(encoding='utf-8') as f:  # noqa: ASYNC230
            await self.pool.execute(f.read())

        self.appinfo = await self.application_info()

        cogs = [m.name for m in iter_modules(['cogs'], prefix='cogs.')]
        cogs.extend(EXTERNAL_COGS)
        for cog in cogs:
            try:
                await self.load_extension(str(cog))
            except commands.ExtensionError as error:
                log.exception(
                    'Ignoring exception in loading %s',
                    cog,
                    exc_info=error,
                )
            else:
                log.info('Loaded %s ', cog)

    @overload
    async def get_context(self, origin: discord.Interaction | discord.Message, /) -> DeContext: ...

    @overload
    async def get_context(self, origin: discord.Interaction | discord.Message, /, *, cls: type[ContextT]) -> ContextT: ...

    async def get_context(
        self,
        origin: discord.Interaction | discord.Message,
        /,
        *,
        cls: type[ContextT] = discord.utils.MISSING,
    ) -> ContextT:
        if cls is discord.utils.MISSING:
            cls = DeContext  # pyright: ignore[reportAssignmentType]
        return await super().get_context(origin, cls=cls)

    @property
    def config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config

    @discord.utils.copy_doc(commands.Bot.is_owner)
    async def is_owner(self, user: discord.abc.User) -> bool:
        return bool(user.id in OWNERS_ID)

    @functools.cached_property
    def logger_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(str(self.config.get('bot', 'webhook')), session=self.session, bot_token=self.token)

    @property
    def guild(self) -> discord.Guild:
        guild = self.get_guild(1262409199552430170)
        if not guild:
            msg = 'Support server not found'
            raise commands.GuildNotFound(msg)
        return guild

    @property
    def user(self) -> discord.ClientUser:
        user = super().user
        if not user:
            msg = "Bot's user not found"
            raise commands.UserNotFound(msg)
        return user

    async def close(self) -> None:
        if hasattr(self, 'pool'):
            await self.pool.close()
        if hasattr(self, 'session'):
            await self.session.close()
        await super().close()
