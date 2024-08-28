from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from utils import (
    Embed,
    LagContext,
    better_string,
)

if TYPE_CHECKING:
    from bot import Lagrange


error_messages = {
    commands.NoPrivateMessage: 'This command cannot be used in DMs',
    commands.NotOwner: 'You cannot run this command. This command is reserved for the developers of the bot.',
    commands.UserInputError: 'The input you have provided is invalid.',
    commands.NSFWChannelRequired: 'This command can only be used in NSFW channels.',
    commands.PrivateMessageOnly: 'This command can only be used in DMs.',
}


class Errors(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    def clean_error_permission(self, permissions: list[str], *, seperator: str, prefix: str) -> str:
        return better_string((prefix + (perm.replace('_', ' ')).capitalize() for perm in permissions), seperator=seperator)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: LagContext, error: commands.CommandError):
        if (
            not ctx.command
            or hasattr(ctx.command, 'on_error')
            or (ctx.cog and ctx.cog._get_overridden_method(commands.Cog.cog_command_error))
        ):
            return None

        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f'Command on cooldown! You can use this command after {error.retry_after:.2f} seconds.',
                delete_after=error.retry_after,
            )

        elif isinstance(error, commands.BadArgument | commands.TooManyArguments):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:grey_tick:1278414780427796631> | Command Failed',
                    description=f'{error}',
                    colour=0xFF0000,
                ),
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:redTick:1237048136527249510> | Missing argument',
                    description=better_string(
                        (
                            f'You did not provide a {error.param.name} argument.',
                            (
                                f'-# - {self.bot.help_command.get_command_signature(ctx.command)}'
                                if self.bot.help_command
                                else None
                            ),
                        ),
                        seperator='\n',
                    ),
                    colour=0xFF0000,
                ),
            )
        elif isinstance(error, commands.MissingPermissions | commands.BotMissingPermissions):
            return await ctx.reply(
                embed=Embed(
                    ctx=ctx,
                    title='<:redTick:1237048136527249510> | Missing Permissions',
                    description=better_string(
                        (
                            f'{"You" if isinstance(error, commands.MissingPermissions) else "I"} are missing the following permissions to run this command:',
                            self.clean_error_permission(list(error.missing_permissions), seperator='\n', prefix='- '),
                        ),
                        seperator='\n',
                    ),
                    colour=0xFF0000,
                ),
            )

        elif isinstance(error, tuple(error_messages.keys())):
            return await ctx.send(
                embed=Embed(
                    ctx=ctx,
                    title='<:status_dnd:1237048172174643200> | Cannot run command',
                    description=f'{error_messages[type(error)]}',
                    colour=0xFF0000,
                ),
            )
        return await ctx.reply(f'Placeholder: {error}')


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(Errors(bot))
