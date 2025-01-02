from __future__ import annotations

import datetime
import logging
from pkgutil import iter_modules
from typing import TYPE_CHECKING, overload

import aiohttp
import asyncpg
import discord
import jishaku
import mystbin
from discord.ext import commands

import config
from utils import BASE_COLOUR, Blacklist, Context

if TYPE_CHECKING:
    from discord.ext.commands._types import ContextT  # pyright: ignore[reportMissingTypeStubs]

import sys

__all__ = ('Mafuyu',)

log: logging.Logger = logging.getLogger(__name__)

jishaku.Flags.FORCE_PAGINATOR = True
jishaku.Flags.HIDE = True
jishaku.Flags.NO_DM_TRACEBACK = True
jishaku.Flags.NO_UNDERSCORE = True


DESCRIPTION = """Yo holy shit a description i wonder what i should put here."""

extensions = [
    'extensions.animanga',
    'extensions.internals',
    'extensions.meta',
]
try:
    import jishaku
except ImportError:
    pass
else:
    extensions.append('jishaku')


class Mafuyu(commands.Bot):
    pool: asyncpg.Pool[asyncpg.Record]
    user: discord.ClientUser

    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.all()
        allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True)
        super().__init__(
            command_prefix=config.DEFAULT_PREFIX,
            case_insensitive=True,
            description=DESCRIPTION,
            strip_after_prefix=True,
            intents=intents,
            max_messages=5000,
            allowed_mentions=allowed_mentions,
        )

        self.token = config.TOKEN

        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': (
                    f'Mafuyu Python/{sys.version_info[0]}.{sys.version_info[1]}'
                    f'.{sys.version_info[2]} aiohttp/{aiohttp.__version__}'
                )
            },
            timeout=aiohttp.ClientTimeout(total=60),
        )
        self.mystbin = mystbin.Client(session=self.session)

        self.prefixes: dict[int, list[str]] = {}
        self.blacklist = Blacklist(self)

        self.maintenance: bool = False
        self.start_time = datetime.datetime.now()
        self.colour = self.color = BASE_COLOUR
        self.initial_extensions = extensions

    async def setup_hook(self) -> None:
        self.appinfo = await self.application_info()
        self.bot_emojis = {emoji.name: emoji for emoji in await self.fetch_application_emojis()}

        cogs = [m.name for m in iter_modules(['cogs'], prefix='cogs.')]
        cogs.append('jishaku')
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
    async def get_context(self, origin: discord.Interaction | discord.Message, /) -> Context: ...

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
            cls = Context  # pyright: ignore[reportAssignmentType]
        return await super().get_context(origin, cls=cls)

    @discord.utils.copy_doc(commands.Bot.is_owner)
    async def is_owner(self, user: discord.abc.User) -> bool:
        return bool(user.id in OWNERS_ID)

    @discord.utils.cached_property
    def logger_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(str(self.config.get('bot', 'webhook')), session=self.session, bot_token=self.token)

    @discord.utils.cached_property
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
