from __future__ import annotations

from typing import TYPE_CHECKING, Self

import discord

from .errors import (
    AlreadyBlacklistedError,
    NotBlacklistedError,
)

__all__ = ('Blacklist',)

if TYPE_CHECKING:
    import datetime

    from discord.abc import Snowflake

    from bot import Mafuyu

    from .context import Context
    from .types import BlacklistBase


class Blacklist:
    blacklist_cache: dict[int, BlacklistBase]

    def __init__(self, bot: Mafuyu, blacklist_cache: dict[int, BlacklistBase]) -> None:
        self.blacklist_cache = blacklist_cache
        self.bot = bot
        self.bot.check_once(self.check)

        self._command_attempts: dict[int, int] = {}
        super().__init__()

    @classmethod
    async def setup(cls, bot: Mafuyu) -> Self:
        entries = await bot.pool.fetch("""SELECT * FROM Blacklists""")

        blacklist_cache: dict[int, BlacklistBase] = {}
        for entry in entries:
            blacklist_cache[entry['snowflake']] = {
                'reason': entry['reason'],
                'lasts_until': entry['lasts_until'],
                'blacklist_type': entry['blacklist_type'],
            }

        return cls(bot, blacklist_cache)

    async def _handle_user_blacklist(self, ctx: Context, user: discord.User | discord.Member, data: BlacklistBase) -> None:
        timestamp_wording = f'until {data["lasts_until"]}' if data['lasts_until'] else 'permanently'
        content = (
            f'{user.mention}, you are blacklisted from using {ctx.bot.user} for `{data['reason']}` {timestamp_wording}. '
            f'If you wish to appeal this blacklist, please join the [Support Server]( {ctx.bot.support_invite} ).'
        )

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.channel.send(content)
            return

        attempt_check = self._command_attempts.get(user.id)

        if not attempt_check:
            self._command_attempts[user.id] = 1
            return

        if attempt_check >= 5:
            await ctx.channel.send(content)
            del self._command_attempts[user.id]
            return

        self._command_attempts[user.id] += 1
        return

    async def check(self, ctx: Context):
        if data := self.is_blacklisted(ctx.author):
            await self._handle_user_blacklist(ctx, ctx.author, data)
            return False
        return True

    def is_blacklisted(self, snowflake: discord.User | discord.Member | discord.Guild) -> BlacklistBase | None:
        return self.blacklist_cache.get(snowflake.id, None)

    async def add(
        self,
        snowflake: discord.User | discord.Guild,
        *,
        reason: str = 'No reason provided',
        lasts_until: datetime.datetime | None = None,
    ) -> dict[Snowflake, BlacklistBase]:
        if self.is_blacklisted(snowflake):
            raise AlreadyBlacklistedError(
                snowflake,
                reason=self.blacklists[snowflake]['reason'],
                until=self.blacklists[snowflake]['lasts_until'],
            )

        sql = """INSERT INTO Blacklists (snowflake, reason, lasts_until, blacklist_type) VALUES ($1, $2, $3, $4);"""
        param = 'user' if isinstance(snowflake, discord.User) else 'guild'
        await self.bot.pool.execute(
            sql,
            snowflake.id,
            reason,
            lasts_until,
            param,
        )
        self.blacklists[snowflake] = {
            'reason': reason,
            'lasts_until': lasts_until,
            'blacklist_type': param,
        }
        return self.blacklists

    async def remove(self, snowflake: discord.User | discord.Guild) -> dict[Snowflake, BlacklistBase]:
        if not self.is_blacklisted(snowflake):
            bsql = """SELECT * FROM Blacklists WHERE snowflake = $1"""
            check = await self.bot.pool.execute(bsql, snowflake.id)
            if check:
                pass
            raise NotBlacklistedError(snowflake)

        sql = """DELETE FROM Blacklists WHERE snowflake = $1"""
        await self.bot.pool.execute(
            sql,
            snowflake.id,
        )
        if snowflake in self.blacklists:
            self.blacklists.pop(snowflake)
        return self.blacklists

    def __repr__(self) -> str:
        return str(self.blacklists)
