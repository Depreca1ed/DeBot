from __future__ import annotations

import datetime
import functools
import logging
import os
from pathlib import Path
from pkgutil import iter_modules
from typing import TYPE_CHECKING, Any, Literal, Self, overload

import aiohttp
import asyncpg
import discord
import jishaku
import mystbin
from discord.ext import commands
from topgg import client, webhook

import config
from utils import (
    Blacklist,
    DeContext,
    PrefixAlreadyPresentError,
    PrefixNotInitialisedError,
    PrefixNotPresentError,
    UnderMaintenanceError,
)

if TYPE_CHECKING:
    from discord.ext.commands._types import ContextT  # pyright: ignore[reportMissingTypeStubs]

import sys

__all__ = ('DeBot',)

log: logging.Logger = logging.getLogger(__name__)

jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True
jishaku.Flags.NO_UNDERSCORE = True


BASE_PREFIX = 'm.'
TEST_PREFIX = 'k.'

OWNERS_ID = [
    688293803613880334,
    263602820496883712,
    651454696208465941,
    412734157819609090,
    606648465065246750,
]

DESCRIPTION = """A low effort bot with a cute design."""

THEME_COLOUR = discord.Colour(0x4B506F)

EXTERNAL_COGS: list[str] = ['jishaku']

PREFIX = BASE_PREFIX if str(os.name) == 'posix' else TEST_PREFIX  # NOTE: Please change this according to your needs.


class DeBot(commands.Bot):
    pool: asyncpg.Pool[asyncpg.Record]
    user: discord.ClientUser

    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.all()
        allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True)

        self.token = config.TOKEN
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': (
                    f'DeBot Python/{sys.version_info[0]}.{sys.version_info[1]}'
                    f'.{sys.version_info[2]} aiohttp/{aiohttp.__version__}'
                )
            },
            timeout=aiohttp.ClientTimeout(total=60),
        )

        self.mystbin = mystbin.Client(session=self.session)
        self.prefixes: dict[int, list[str]] = {}
        self.blacklist = Blacklist(self)
        self.maintenance = False
        self.check_once(self.check_maintenance)
        super().__init__(
            description=DESCRIPTION,
            command_prefix=self.get_prefix,  # pyright: ignore[reportArgumentType]
            case_insensitive=True,
            strip_after_prefix=True,
            intents=intents,
            max_messages=5000,
            allowed_mentions=allowed_mentions,
        )

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

        self.topgg = client.DBLClient(self, self.config.get('bot', 'topgg'), autopost=True, post_shard_count=True)
        self.topggwebhook = webhook.WebhookManager(self).dbl_webhook('/debotdbl', auth_key='debotdbl')
        await self.topggwebhook.run(8080)

        cogs = [m.name for m in iter_modules(['cogs'], prefix='cogs.')]
        cogs.extend(EXTERNAL_COGS)
        for cog in cogs:
            try:
                await self.load_extension(str(cog))
            except commands.ExtensionError as error:
                self.log.exception(
                    'Ignoring exception in loading %s',
                    cog,
                    exc_info=error,
                )
            else:
                self.log.info('Loaded %s ', cog)

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

    async def close(self) -> None:
        if hasattr(self, 'pool'):
            await self.pool.close()
        if hasattr(self, 'session'):
            await self.session.close()
        if hasattr(self, 'topgg'):
            await self.topgg.close()
        if hasattr(self, 'topggwebhook'):
            await self.topggwebhook.close()
        await super().close()
