from __future__ import annotations

import contextlib
import traceback
from typing import TYPE_CHECKING, Any

import discord
import mystbin
from discord.ext import commands

from utils import OWNERS_ID, Embed, FeatureDisabled, LagContext

if TYPE_CHECKING:
    from bot import Lagrange


def get_command_signature(context: LagContext, command: commands.Command[Any, ..., Any], /) -> str:
    """Get the command signature of a command, this is from the help command
    Parameters
    ------------
    context:
        The context
    command: :class:`Command`
        The command to get the signature of.

    Returns
    --------
    :class:`str`
        The signature for the command.
    """
    parent: commands.Group[Any, ..., Any] | None = command.parent  # pyright: ignore[reportAssignmentType]
    entries: list[str] = []
    while parent is not None:
        if not parent.signature or parent.invoke_without_command:
            entries.append(parent.name)
        else:
            entries.append(parent.name + ' ' + parent.signature)
        parent = parent.parent  # pyright: ignore[reportAssignmentType]
    parent_sig = ' '.join(reversed(entries))

    if len(command.aliases) > 0:
        aliases = '|'.join(command.aliases)
        fmt = f'[{command.name}|{aliases}]'
        if parent_sig:
            fmt = parent_sig + ' ' + fmt
        alias = fmt
    else:
        alias = command.name if not parent_sig else parent_sig + ' ' + command.name

    return f'{context.clean_prefix}{alias} {command.signature}'


def clean_error_message(error_string: str) -> str:
    """This is a function used for cleaning the arguments of the errors like permissions, param names, etc."""
    new_error_string = error_string.replace('_', ' ')
    return new_error_string.capitalize()


class Errors(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: LagContext, error: Exception) -> Any:  # noqa: ANN401, C901, PLR0911, PLR0912
        if ctx.cog and commands.Cog._get_overridden_method(ctx.cog.cog_command_error):
            return None

        if hasattr(ctx.command, 'on_error'):
            return None

        if isinstance(error, commands.CommandNotFound):
            if ctx.author.id in OWNERS_ID:
                return None
            with contextlib.suppress(discord.HTTPException):
                return await ctx.message.add_reaction('<:status_dnd:1237048172174643200>')
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f'Command on cooldown! You can use this command after {error.retry_after:.2f} seconds.')
        if ctx.command is None:
            await self.bot.logger_webhook.send('Yup the assertion error triggered yet again less go')
        assert ctx.command is not None
        # Check for if bot has perms to send embeds since we need that, if it doesnt we will raise an error for the BotMissingPermissions. Unfortunately due to lack of programming knowledge I had to copy the text from that specified error and put my own shit here
        if (
            ctx.guild
            and [r for r in ctx.guild.me.roles if r]
            and ctx.channel.permissions_for(ctx.guild.me).embed_links is False
        ):
            permissions = '\n'.join([f"- {clean_error_message('embed_links')}"])  # The string used in the command
            embed = Embed(
                title='<:redTick:1237048136527249510> | Missing Permissions',
                description=f'I am missing the following permissions to run this command.\n{permissions}',
                colour=0xFF0000,
                ctx=ctx,
            )
            channel = (
                ctx.channel
                if isinstance(ctx.author, discord.Member) and ctx.channel.permissions_for(ctx.author).send_messages is True
                else ctx.author
            )
            return (
                await channel.send(embed=embed)
                if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).embed_links is True
                else await channel.send(content=embed.description)
            )

        # Few Argument checks not much
        if isinstance(error, commands.BadArgument):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:redTick:1237048136527249510> | Invalid Argument',
                    description=f'{error}',
                    colour=0xFF0000,
                ),
            )
        if isinstance(error, commands.TooManyArguments):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:redTick:1237048136527249510> | Too Many Arguments',
                    description=f'{error}',
                    colour=0xFF0000,
                ),
            )
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:redTick:1237048136527249510> | Missing argument',
                    description=f'You did not provide a {error.param.name} argument. \n- How to use the command:\n  - `{get_command_signature(ctx, ctx.command)}`',
                    colour=0xFF0000,
                ),
            )
        # Permission checks
        if isinstance(error, commands.MissingPermissions):
            permissions = '\n'.join(
                [f'- {clean_error_message(permission)}' for permission in error.missing_permissions],
            )  # The string used in the command
            embed = Embed(
                ctx=ctx,
                title='<:redTick:1237048136527249510> | Missing Permissions',
                description=f'You are missing the following permissions to run this command.\n{permissions}',
                colour=0xFF0000,
            )
            channel = (
                ctx.channel
                if isinstance(ctx.author, discord.Member) and ctx.channel.permissions_for(ctx.author).send_messages is True
                else ctx.author
            )
            return (
                await channel.send(embed=embed)
                if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).embed_links is True
                else await channel.send(content=embed.description)
            )
        if isinstance(error, commands.BotMissingPermissions):
            permissions = '\n'.join(
                [f'- {clean_error_message(permission)}' for permission in error.missing_permissions],
            )  # The string used in the command
            embed = Embed(
                ctx=ctx,
                title='<:redTick:1237048136527249510> | Missing Permissions',
                description=f'I am missing the following permissions to run this command.\n{permissions}',
                colour=0xFF0000,
            )
            channel = (
                ctx.channel
                if isinstance(ctx.author, discord.Member) and ctx.channel.permissions_for(ctx.author).send_messages is True
                else ctx.author
            )
            return (
                await channel.send(embed=embed)
                if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).embed_links is True
                else await channel.send(content=embed.description)
            )

        error_messages = {
            commands.NoPrivateMessage: 'This command cannot be used in DMs',
            commands.NotOwner: 'You cannot run this command. This command is reserved for the developers of the bot.',
            commands.UserInputError: 'The input you have provided is invalid.',
            commands.NSFWChannelRequired: 'This command can only be used in NSFW channels.',
            commands.PrivateMessageOnly: 'This command can only be used in DMs.',
            FeatureDisabled: 'This feature is not enabled in this server.',
        }
        message = error_messages.get(type(error), None)  # type: ignore  # noqa: PGH003
        if message:
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:status_dnd:1237048172174643200> | Cannot run command',
                    description=f'{message}',
                    colour=0xFF0000,
                ),
            )
        else:  # noqa: RET505
            if isinstance(error, commands.CommandError):
                error_message = ''.join(
                    traceback.format_exception(type(error), error, error.__traceback__),
                )  # The traceback message, not to be sent in its purity to anything except the database

                if len(error_message) >= 1990:  # noqa: PLR2004
                    error_link = await self.bot.mystbin_cli.create_paste(
                        files=[mystbin.File(filename='error.py', content=error_message)],
                    )

                    post_message = f'Error message was too long to be shown in this embed. \n- [Link to Error]({error_link})'
                else:
                    post_message = f'```py\n{error_message}```'
                error_embed = Embed(ctx=ctx, title='Error', description=post_message, colour=0x000000)
                extras = [
                    f'- **Command -** {ctx.command.qualified_name}',
                    f'- **Invoked as -** {ctx.message.clean_content}',
                    f'- **Short error**\n```py\n{error!s}```',
                ]
                error_embed.add_field(name='Extra', value='\n'.join(extras), inline=False)
                return await self.bot.logger_webhook.send(embed=error_embed)
            return None


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Errors(bot))
