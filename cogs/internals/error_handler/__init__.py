from __future__ import annotations

import difflib

from discord.ext import commands

from utils import DeContext, better_string

from .helpers import clean_error, generate_error_objects, make_embed
from .views import MissingArgumentHandler

defaults = (
    commands.UserInputError,
    commands.DisabledCommand,
    commands.MaxConcurrencyReached,
    commands.CommandOnCooldown,
    commands.PrivateMessageOnly,
    commands.NoPrivateMessage,
    commands.NotOwner,
    commands.NSFWChannelRequired,
    commands.TooManyArguments,
)


async def error_handler(ctx: DeContext, error: commands.CommandError) -> None:
    if (ctx.command and ctx.command.has_error_handler()) or (ctx.cog and ctx.cog.has_error_handler()):
        return

    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound) or not ctx.command:
        cmd = ctx.invoked_with
        if not cmd:
            return

        cmd_list = [command.name for command in ctx.bot.commands]
        possible_cmd = difflib.get_close_matches(cmd, cmd_list, n=1)
        if possible_cmd:
            embed = make_embed(
                title='Command Not Found',
                description=f'Could not find a command with that name. Perhaps you meant, `{possible_cmd[0]}`?',
                ctx=ctx,
            )
            await ctx.reply(embed=embed, delete_after=10.0)

        return

    if isinstance(error, commands.MissingRequiredArgument | commands.MissingRequiredAttachment):
        param_name = error.param.displayed_name or error.param.name
        embed = make_embed(
            title=f'Missing {param_name} argument!',
            description=better_string(
                (
                    f'You did not provide a **__{param_name}__** argument.',
                    f'> -# `{ctx.clean_prefix}{ctx.command} {ctx.command.signature}`',
                ),
                seperator='\n',
            ),
            ctx=ctx,
        )

        if isinstance(error, commands.MissingRequiredArgument):
            view = MissingArgumentHandler(error, ctx)
            view.prev_message = await ctx.reply(embed=embed, view=view)
            return

        await ctx.reply(embed=embed)
        return

    if isinstance(
        error,
        commands.MissingPermissions
        | commands.BotMissingPermissions
        | commands.MissingAnyRole
        | commands.MissingRole
        | commands.BotMissingAnyRole
        | commands.BotMissingRole,
    ):
        person = (
            'You'
            if isinstance(
                error,
                commands.MissingPermissions | commands.MissingAnyRole | commands.MissingRole,
            )
            else 'I'
        )
        error_type_wording = (
            'permissions' if isinstance(error, commands.MissingPermissions | commands.BotMissingPermissions) else 'roles'
        )
        final_iter = generate_error_objects(error)

        content = better_string(
            (
                f'{person} are missing the following {error_type_wording} to run this command:',
                clean_error(final_iter, seperator='\n', prefix='- '),
            ),
            seperator='\n',
        )

        embed = make_embed(
            ctx=ctx,
            title=f'Missing {error_type_wording.title()}',
            description=content,
        )
        await ctx.reply(embed=embed)
        return

    if type(error) in defaults:
        await ctx.reply(str(error), delete_after=getattr(error, 'retry_after', None))
        return

    # From here we handle unexpected errors.
    # The process is as follows
    # > Check if error has happened before
    # > If not, register the error
    # > Else, dont register
    # Additional functionality include:
    # > Allowing the user to know when what is fixed or will be fixed
    # > Allow user to see the error. If they wish to fix it then allow them to PR (requires getsource wrt github)
    # > Lastly do all of this in a good manner

    ctx.bot.log.exception(
        'Ignoring exception in running %s',
        ctx.command,
        exc_info=error,
    )

    check = await ctx.bot.pool.fetchrow(
        """SELECT * FROM Errors WHERE command = $1 AND error = $2 AND fixed = $3""",
        ctx.command.qualified_name,
        str(error),
        False,
    )

    # Temp.
