from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from datetime import datetime

    import discord

__all__ = (
    'BlacklistedGuild',
    'BlacklistedUser',
    'FeatureDisabled',
    'AlreadyBlacklisted',
    'PrefixAlreadyPresent',
    'PrefixNotInitialised',
    'PrefixNotPresent',
    'NotBlacklisted',
    'UnderMaintenance',
    'LagrangeError',
)


class LagrangeError(Exception): ...


class FeatureDisabled(commands.CheckFailure, LagrangeError):
    def __init__(self) -> None:
        super().__init__('This feature is not enabled in this server.')


class PrefixNotInitialised(commands.CommandError, LagrangeError):
    def __init__(self, guild: discord.Guild) -> None:
        super().__init__(f'Prefixes were not initialised for {guild.id}')


class PrefixAlreadyPresent(commands.CommandError, LagrangeError):
    def __init__(self, prefix: str) -> None:
        super().__init__(f"'{prefix} is an already present prefix.'")


class PrefixNotPresent(commands.CommandError, LagrangeError):
    def __init__(self, prefix: str, guild: discord.Guild) -> None:
        super().__init__(f'{prefix} is not present in guild: {guild.id}')


class BlacklistedUser(commands.CheckFailure, LagrangeError):
    def __init__(self, snowflake: discord.User | discord.Member, reason: str, until: datetime | None) -> None:
        super().__init__(f'{snowflake} is blacklisted for {reason} until {until}')


class BlacklistedGuild(commands.CheckFailure, LagrangeError):
    def __init__(self, snowflake: discord.Guild, reason: str, until: datetime | None) -> None:
        super().__init__(f'{snowflake} is blacklisted for {reason} until {until}')


class AlreadyBlacklisted(commands.CommandError, LagrangeError):
    def __init__(self, snowflake: discord.User | discord.Guild, reason: str, until: datetime | None) -> None:
        super().__init__(f'{snowflake} is already blacklisted for {reason} until {until}')


class NotBlacklisted(commands.CommandError, LagrangeError):
    def __init__(self, snowflake: discord.User | discord.Guild) -> None:
        super().__init__(f'{snowflake} is not blacklisted.')


class UnderMaintenance(commands.CheckFailure, LagrangeError):
    def __init__(self) -> None:
        super().__init__('The bot is currently under maintenance.')


# TODO(Depreca1ed): All of these are not supposed to be commands.CommandError. Change them to actual errors which mostly likely suit their use case
