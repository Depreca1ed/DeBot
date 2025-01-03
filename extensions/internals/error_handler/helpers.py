from __future__ import annotations

from typing import TYPE_CHECKING

import discord
import mystbin
from discord.ext import commands

from utils import better_string
from utils.embed import Embed


if TYPE_CHECKING:
    import asyncpg

    from bot import Mafuyu

__all__ = ('clean_error', 'generate_error_objects', 'logger_embed', 'make_embed')


def clean_error(objects: list[str] | str, *, seperator: str, prefix: str) -> str:
    """
    Return a string with the given objects organised.

    Parameters
    ----------
    objects : list[str]
        List of iterables to prettify, this should be either list of roles or permissions.
    seperator : str
        String which seperates the given objects.
    prefix : str
        String which will be at the start of every object

    Returns
    -------
    str
        The generated string with the given parameters

    """
    return (
        better_string(
            (prefix + f"{(perm.replace('_', ' ')).capitalize()}" for perm in objects),
            seperator=seperator,
        )
        if objects is not str
        else prefix + objects
    )


def generate_error_objects(
    error: commands.MissingPermissions
    | commands.BotMissingPermissions
    | commands.MissingAnyRole
    | commands.MissingRole
    | commands.BotMissingAnyRole
    | commands.BotMissingRole,
) -> list[str] | str:
    """
    Generate a list or string of given objects from the error.

    Note
    ----
    Only to be used in error handler for these errors.


    Parameters
    ----------
    error : commands.MissingPermissions
      | commands.BotMissingPermissions
      | commands.MissingAnyRole
      | commands.MissingRole
      | commands.BotMissingAnyRole
      | commands.BotMissingRole
        The error used to make the objects

    Returns
    -------
    list[str] | str
        The list or string made from given errors.

    Raises
    ------
    ValueError
        Raised when the string was empty.

    """
    missing_roles = (
        [str(f'<@&{role_id}>' if role_id is int else role_id) for role_id in error.missing_roles]
        if isinstance(error, commands.MissingAnyRole | commands.BotMissingAnyRole)
        else None
    )

    missing_role = (
        str(f'<@&{error.missing_role}>' if error.missing_role is int else error.missing_role)
        if isinstance(error, commands.MissingRole | commands.BotMissingRole)
        else None
    )

    missing_permissions = (
        error.missing_permissions
        if isinstance(error, commands.MissingPermissions | commands.BotMissingPermissions)
        else None
    )

    missings = missing_roles or missing_role or missing_permissions
    if not missings:
        msg = 'Expected Not-None value'
        raise ValueError(msg)

    return missings


async def logger_embed(bot: Mafuyu, record: asyncpg.Record) -> Embed:
    error_link = await bot.mystbin_cli.create_paste(
        files=(
            mystbin.File(
                filename=f'error{record["id"]}.py',
                content=record['full_error'],
            ),
        )
    )

    logger_embed = Embed(
        title=f'Error #{record["id"]}',
        description=f"""```py\n{record['full_error']}```"""
        if len(record['full_error']) < CHAR_LIMIT
        else 'Error message was too long to be shown',
        colour=0xFF0000 if record['fixed'] is False else 0x00FF00,
        url=error_link.url,
    )

    logger_embed.add_field(
        value=better_string(
            (
                f'- **Command:** `{record['command']}`',
                f'- **User:** {bot.get_user(record['user_id'])}',
                f'- **Guild:** {bot.get_guild(record['guild']) if record['guild'] else "N/A"}',
                f'- **URL: ** [Jump to message]({record['message_url']})',
                f'- **Occured: ** {discord.utils.format_dt(record['occured_when'], "f")}',
            ),
            seperator='\n',
        )
    )
    return logger_embed
