from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord

from .errors import (
    AlreadyBlacklistedError,
    BlacklistedGuildError,
    BlacklistedUserError,
    NotBlacklistedError,
)

__all__ = ('Blacklist',)

if TYPE_CHECKING:
    import datetime

    from discord.abc import Snowflake

    from bot import DeBot

    from .context import DeContext
    from .types import BlacklistBase


class Blacklist:
    blacklists: dict[Snowflake, BlacklistBase]

    def __init__(self, bot: DeBot) -> None:
        self.blacklists = {}
        self.bot = bot
        self.bot.check_once(self.check)
        super().__init__()

    async def check(self, ctx: DeContext) -> Literal[True]:
        pass

    def is_blacklisted(self, snowflake: discord.Member | discord.User | discord.Guild) -> bool:
        return bool(self.blacklists.get(snowflake))

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
