from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord

from .errors import AlreadyBlacklisted, BlacklistedGuild, BlacklistedUser, NotBlacklisted

if TYPE_CHECKING:
    import datetime

    from discord.abc import Snowflake

    from bot import Lagrange

    from .context import LagContext
    from .types import BlacklistBase


class Blacklist:
    def __init__(self, bot: Lagrange) -> None:
        self.blacklist: dict[Snowflake, BlacklistBase] = {}
        self.bot = bot
        self.bot.check_once(self.check_blacklist)

    async def check_blacklist(self, ctx: LagContext) -> Literal[True]:
        if ctx.guild and self.is_blacklisted(ctx.guild):
            raise BlacklistedGuild(
                ctx.guild,
                reason=self.blacklist[ctx.guild]['reason'],
                until=self.blacklist[ctx.guild]['lasts_until'],
            )
        if ctx.author and self.is_blacklisted(ctx.author):
            raise BlacklistedUser(
                ctx.author,
                reason=self.blacklist[ctx.author]['reason'],
                until=self.blacklist[ctx.author]['lasts_until'],
            )

        return True

    def is_blacklisted(self, snowflake: discord.Member | discord.User | discord.Guild) -> bool:
        return bool(self.blacklist.get(snowflake))

    async def add_blacklist(
        self,
        snowflake: discord.User | discord.Guild,
        *,
        reason: str = 'No reason provided',
        lasts_until: datetime.datetime | None = None,
    ) -> dict[Snowflake, BlacklistBase]:
        if self.is_blacklisted(snowflake):
            raise AlreadyBlacklisted(
                snowflake,
                reason=self.blacklist[snowflake]['reason'],
                until=self.blacklist[snowflake]['lasts_until'],
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
        self.blacklist[snowflake] = {'reason': reason, 'lasts_until': lasts_until, 'blacklist_type': param}
        return self.blacklist

    async def remove_blacklist(self, snowflake: discord.User | discord.Guild) -> dict[Snowflake, BlacklistBase]:
        if not self.is_blacklisted(snowflake):
            raise NotBlacklisted(snowflake)

        sql = """DELETE FROM Blacklists WHERE snowflake = $1"""
        param: str = 'user' if isinstance(snowflake, discord.User) else 'guild'
        await self.bot.pool.execute(
            sql,
            snowflake.id,
            param,
        )

        self.blacklist.pop(snowflake)
        return self.blacklist
