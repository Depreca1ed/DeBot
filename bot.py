from __future__ import annotations

import datetime
import functools
import logging
from itertools import product
from pathlib import Path
from pkgutil import iter_modules
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self

import aiohttp
import asyncpg
import discord
import jishaku
import mystbin
from discord.ext import commands

from utils import (
    BASE_PREFIX,
    BOT_TOKEN,
    DESCRIPTION,
    OWNERS_ID,
    POSTGRES_CREDENTIALS,
    SERVER_INVITE,
    THEME_COLOUR,
    WEBHOOK_URL,
    AlreadyBlacklisted,
    BlacklistedGuild,
    BlackListedTypes,
    BlacklistedUser,
    NotBlacklisted,
    PrefixAlreadyPresent,
    PrefixNotInitialised,
    PrefixNotPresent,
    UnderMaintenance,
)

__all__ = ('Lagrange',)

log: logging.Logger = logging.getLogger(__name__)

jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True
jishaku.Flags.USE_ANSI_ALWAYS = True
jishaku.Flags.NO_UNDERSCORE = True

EXTERNAL_COGS: list[str] = ['jishaku']


class Lagrange(commands.Bot):
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
    blacklist: BlackListedTypes
    maintenance: bool
    appinfo: discord.AppInfo
    support_server: discord.Invite
    banner: discord.Asset

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        intents: discord.Intents = discord.Intents.all()
        self.token = BOT_TOKEN  # The thing everyone looks for; A way to control their beloved waifu: Lagrange
        self.session = aiohttp.ClientSession()
        self.mystbin_cli = mystbin.Client()
        self.load_time = datetime.datetime.now(datetime.UTC)
        self.prefixes: dict[int, list[str]] = {}
        self.blacklist = {'guild': [], 'user': []}
        self.maintenance = False
        super().__init__(
            description=DESCRIPTION,
            command_prefix=self.get_prefix,  # pyright: ignore[reportArgumentType]
            case_insensitive=True,
            strip_after_prefix=True,
            intents=intents,
            max_messages=5000,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True),
            *args,
            **kwargs,
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
            raise PrefixAlreadyPresent(prefix)

        await self.pool.execute("""INSERT INTO Prefixes VALUES ($1, $2)""", guild.id, prefix)
        if not self.prefixes.get(guild.id):
            self.prefixes[guild.id] = [prefix]
            return self.prefixes[guild.id]
        self.prefixes[guild.id].append(prefix)

        return self.prefixes[guild.id]

    async def remove_prefix(self, guild: discord.Guild, prefix: str) -> list[str] | None:
        if not self.prefixes.get(guild.id):
            raise PrefixNotInitialised(guild)

        if prefix not in self.prefixes[guild.id]:
            raise PrefixNotPresent(prefix, guild)

        await self.pool.execute(
            """DELETE FROM Prefixes WHERE guild = $1 AND prefix = $2""",
            guild.id,
            prefix,
        )
        self.prefixes[guild.id].remove(prefix)
        if not self.prefixes[guild.id]:
            self.prefixes.pop(guild.id)  # NOTE: This is an excessive cleaner. Unsure if it should be present
            return None
        return self.prefixes[guild.id]

    async def clear_prefix(self, guild: discord.Guild) -> None:
        if not self.prefixes.get(guild.id):
            raise PrefixNotInitialised(guild)

        await self.pool.execute("""DELETE FROM Prefixes WHERE guild = $1""", guild.id)

        self.prefixes.pop(guild.id)

    async def get_prefix_list(self, message: discord.Message) -> list[str]:
        prefixes = [BASE_PREFIX]
        if message.guild and self.prefixes.get(message.guild.id):
            prefixes.extend(self.prefixes[message.guild.id])

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def check_blacklist(self, ctx: commands.Context[Self]) -> Literal[True]:
        if ctx.guild and self.is_blacklisted(ctx.guild):
            raise BlacklistedGuild(ctx.guild)
        if ctx.author and self.is_blacklisted(ctx.author):
            raise BlacklistedUser(ctx.author)

        return True

    def is_blacklisted(self, snowflake: discord.Member | discord.User | discord.Guild) -> bool:  # NOTE: YUP! DO CHECK THIS
        return bool(
            (isinstance(snowflake, discord.User | discord.Member) and snowflake.id in self.blacklist['user'])
            or (isinstance(snowflake, discord.Guild) and snowflake.id in self.blacklist['guild']),
        )

    async def add_blacklist(self, snowflake: discord.User | discord.Guild) -> list[int]:
        if self.is_blacklisted(snowflake):
            raise AlreadyBlacklisted(snowflake)

        sql = """INSERT INTO Blacklists (id, type) VALUES ($1, $2)"""
        param: str = 'user' if isinstance(snowflake, discord.User) else 'guild'
        await self.pool.execute(
            sql,
            (
                snowflake.id,
                param,
            ),
        )
        self.blacklist[param].append(snowflake.id)
        return self.blacklist[param]

    async def remove_blacklist(self, snowflake: discord.User | discord.Guild) -> list[int]:
        if not self.is_blacklisted(snowflake):
            raise NotBlacklisted(snowflake)

        sql = """DELETE FROM Blacklists WHERE id = ? AND type = ?"""
        param: str = 'user' if isinstance(snowflake, discord.User) else 'guild'
        await self.pool.execute(
            sql,
            snowflake.id,
            param,
        )
        self.blacklist[param].append(snowflake.id)
        return self.blacklist[param]

    async def check_maintenance(self, ctx: commands.Context[Self]) -> Literal[True]:
        if self.maintenance is True and not await self.is_owner(ctx.author):
            raise UnderMaintenance
        return True

    async def toggle_maintenance(self, toggle: bool | None = None) -> bool:
        if toggle:
            self.maintenance = toggle
            return self.maintenance
        self.maintenance = self.maintenance is False
        return self.maintenance

    async def setup_hook(self) -> None:
        # Close your eyes for the next 6 lines or something and look at https://github.com/itswilliboy/Harmony/blob/master/bot.py#L79-L84 instead
        credentials: dict[str, Any] = POSTGRES_CREDENTIALS
        pool: asyncpg.Pool[asyncpg.Record] | None = await asyncpg.create_pool(**credentials)
        if not pool or pool and pool._closed:
            msg = 'Pool is closed'
            raise RuntimeError(msg)
        self.pool = pool

        with Path('schema.sql').open(encoding='utf-8') as f:  # noqa: ASYNC230
            await self.pool.execute(f.read())

        self.appinfo = await self.application_info()
        self.invite = await self.fetch_invite(SERVER_INVITE)
        banner = (await self.fetch_user(self.user.id)).banner
        assert banner is not None
        self.banner = banner

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

        self.check_once(self.check_blacklist)
        self.check_once(self.check_maintenance)

    @discord.utils.copy_doc(commands.Bot.is_owner)
    async def is_owner(self, user: discord.abc.User) -> bool:
        return bool(user.id in OWNERS_ID)

    @functools.cached_property
    def logger_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(WEBHOOK_URL, session=self.session, bot_token=self.token)

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
        if hasattr(self, 'pool'):
            await self.pool.close()
        if hasattr(self, 'session'):
            await self.session.close()
        await super().close()
