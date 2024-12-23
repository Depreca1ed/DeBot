from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from datetime import datetime

    import discord

__all__ = (
    'AlreadyBlacklistedError',
    'BlacklistedGuildError',
    'BlacklistedUserError',
    'DeBotError',
    'FeatureDisabledError',
    'NotBlacklistedError',
    'PrefixAlreadyPresentError',
    'PrefixNotInitialisedError',
    'PrefixNotPresentError',
    'UnderMaintenanceError',
)


class DeBotError(Exception): ...


class FeatureDisabledError(commands.CheckFailure, DeBotError):
    def __init__(self) -> None:
        super().__init__('This feature is not enabled in this server.')


class PrefixNotInitialisedError(commands.CommandError, DeBotError):
    def __init__(self, guild: discord.Guild) -> None:
        super().__init__(f'Prefixes were not initialised for {guild.id}')


class PrefixAlreadyPresentError(commands.CommandError, DeBotError):
    def __init__(self, prefix: str) -> None:
        super().__init__(f"'{prefix} is an already present prefix.'")


class PrefixNotPresentError(commands.CommandError, DeBotError):
    def __init__(self, prefix: str, guild: discord.Guild) -> None:
        super().__init__(f'{prefix} is not present in guild: {guild.id}')


class BlacklistedUserError(commands.CheckFailure, DeBotError):
    def __init__(
        self,
        reason: str,
        until: datetime | None,
    ) -> None:
        string = 'You have been blacklisted'
        reason = f' for {reason}' if reason != 'No reason provided' else ''
        until = f' until {until}' if until else ' permanently'
        super().__init__(string + reason + until)


class BlacklistedGuildError(commands.CheckFailure, DeBotError):
    def __init__(self, reason: str, until: datetime | None) -> None:
        string = 'Your guild has been blacklisted'
        reason = f' for {reason}' if reason != 'No reason provided' else ''
        until = f' until {until}' if until else ' permanently'
        super().__init__(string + reason + until)


class AlreadyBlacklistedError(commands.CommandError, DeBotError):
    def __init__(
        self,
        snowflake: discord.User | discord.Guild,
        reason: str,
        until: datetime | None,
    ) -> None:
        string = f'{snowflake} is already blacklisted'
        reason = f' for {reason}' if reason != 'No reason provided' else ''
        until = f' until {until}' if until else ' permanently'
        super().__init__(string + reason + until)


class NotBlacklistedError(commands.CommandError, DeBotError):
    def __init__(self, snowflake: discord.User | discord.Guild) -> None:
        super().__init__(f'{snowflake} is not blacklisted.')


class UnderMaintenanceError(commands.CheckFailure, DeBotError):
    def __init__(self) -> None:
        super().__init__('The bot is currently under maintenance.')


class WaifuNotFoundError(commands.CommandError, DeBotError):
    def __init__(self, waifu: str | None = None) -> None:
        if waifu:
            waifu = waifu.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(f'Could not find any results for {waifu}')
        else:
            super().__init__(message='Could not find any results')


# TODO(Depreca1ed): All of these are not supposed to be CommandError. Change them to actual errors  # noqa: FIX002, TD003
