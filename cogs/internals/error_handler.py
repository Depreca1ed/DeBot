from __future__ import annotations

import traceback

import discord
import mystbin
from discord.ext import commands

from utils import (
    BaseCog,
    BlacklistedGuild,
    BlacklistedUser,
    Embed,
    FeatureDisabled,
    DeContext,
    DeBotError,
    UnderMaintenance,
    better_string,
)


class ErrorHandler(BaseCog):
    def clean_error_permission(self, permissions: list[str], *, seperator: str, prefix: str) -> str:
        return better_string((prefix + (perm.replace('_', ' ')).capitalize() for perm in permissions), seperator=seperator)

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: DeContext, error: commands.CommandError) -> None | discord.Message:
        error_messages = {
            commands.NoPrivateMessage: 'This command cannot be used in DMs',
            commands.NotOwner: 'You cannot run this command. This command is reserved for the developers of the bot.',
            commands.UserInputError: 'The input you have provided is invalid.',
            commands.NSFWChannelRequired: 'This command can only be used in NSFW channels.',
            commands.PrivateMessageOnly: 'This command can only be used in DMs.',
            commands.BadArgument: str(error),
            commands.TooManyArguments: str(error),
        }

        if (
            not ctx.command
            or hasattr(ctx.command, 'on_error')
            or (ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error))
        ):
            return None
        elif isinstance(error, DeBotError):
            if (isinstance(ctx.channel, discord.DMChannel) and isinstance(error, BlacklistedUser)) or isinstance(
                error,
                UnderMaintenance | FeatureDisabled,
            ):
                await ctx.reply(content=str(error))

            elif ctx.guild and isinstance(error, BlacklistedGuild):
                await ctx.guild.leave()

            return None

        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f'Command on cooldown! You can use this command after {error.retry_after:.2f} seconds.',
                delete_after=error.retry_after,
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            content = better_string(
                (
                    f'You did not provide a {error.param.name} argument.',
                    (f'-# - {self.bot.help_command.get_command_signature(ctx.command)}' if self.bot.help_command else None),
                ),
                seperator='\n',
            )
            embed = Embed(
                ctx=ctx,
                title='<:redTick:1237048136527249510> | Missing argument',
                description=content,
                colour=0xFF0000,
            )
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions | commands.BotMissingPermissions):
            content = better_string(
                (
                    f'{"You" if isinstance(error, commands.MissingPermissions) else "I"} are missing the following permissions to run this command:',
                    self.clean_error_permission(list(error.missing_permissions), seperator='\n', prefix='- '),
                ),
                seperator='\n',
            )
            embed = Embed(
                ctx=ctx,
                title='<:redTick:1237048136527249510> | Missing Permissions',
                description=content,
                colour=0xFF0000,
            )
            return await ctx.reply(embed=embed)
        elif isinstance(error, tuple(error_messages.keys())):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:status_dnd:1237048172174643200> | Cannot run command',
                    description=f'{error_messages[type(error)]}',
                    colour=0xFF0000,
                ),
            )

        await ctx.reply(content=str(error) + '\n-# Developers have been informed')
        exc = f"```py\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```"
        exc_link = (
            await self.bot.mystbin_cli.create_paste(
                files=[
                    mystbin.File(filename='error', content=exc),
                ],
            )
            if len(exc) > 2000
            else None
        )

        embed = Embed(title=error.__class__.__name__, description=exc, url=exc_link, colour=0x000000, ctx=ctx)
        embed.add_field(
            value=better_string(
                [
                    f'> - **User: **{ctx.author!s}',
                    f'> - **Server: **{ctx.guild.name if ctx.guild else 'No guild'!s}',
                    f'> - **Command: **{ctx.command.name}',
                ],
                seperator='\n',
            ),
        )
        return await self.bot.logger_webhook.send(embed=embed)
