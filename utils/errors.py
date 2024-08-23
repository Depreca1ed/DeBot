from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
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
)


class FeatureDisabled(commands.CheckFailure):
    pass


class PrefixNotInitialised(commands.CommandError):
    def __init__(self, guild: discord.Guild) -> None:
        super().__init__(f'Prefixes were not initialised for {guild.id}')


class PrefixAlreadyPresent(commands.CommandError):
    def __init__(self, prefix: str) -> None:
        super().__init__(f"'{prefix} is an already present prefix.'")


class PrefixNotPresent(commands.CommandError):
    def __init__(self, prefix: str, guild: discord.Guild) -> None:
        super().__init__(f'{prefix} is not present in guild: {guild.id}')


class BlacklistedUser(commands.CheckFailure):
    def __init__(self, snowflake: discord.User | discord.Member) -> None:
        super().__init__(f'{snowflake} is blacklisted')


class BlacklistedGuild(commands.CheckFailure):
    def __init__(self, snowflake: discord.Guild) -> None:
        super().__init__(f'{snowflake} is blacklisted.')


class AlreadyBlacklisted(commands.CommandError):
    def __init__(self, snowflake: discord.User | discord.Guild) -> None:
        super().__init__(f'{snowflake} is already blacklisted')


class NotBlacklisted(commands.CommandError):
    def __init__(self, snowflake: discord.User | discord.Guild) -> None:
        super().__init__(f'{snowflake} is not blacklisted.')


class UnderMaintenance(commands.CheckFailure):
    def __init__(self) -> None:
        super().__init__('The bot is currently under maintenance.')


# TODO(Depreca1ed): All of these are not supposed to be commands.CommandError. Change them to actual errors which mostly likely suit their use case
