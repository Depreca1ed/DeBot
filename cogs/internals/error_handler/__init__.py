from __future__ import annotations

import datetime
import difflib
import traceback

import discord
import mystbin
from discord.ext import commands

from utils import DeContext, Embed, better_string

from .helpers import clean_error, generate_error_objects, make_embed
from .views import ErrorView, MissingArgumentHandler

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
            'You are'
            if isinstance(
                error,
                commands.MissingPermissions | commands.MissingAnyRole | commands.MissingRole,
            )
            else 'I am'
        )
        error_type_wording = (
            'permissions' if isinstance(error, commands.MissingPermissions | commands.BotMissingPermissions) else 'roles'
        )
        final_iter = generate_error_objects(error)

        content = better_string(
            (
                f'{person} missing the following {error_type_wording} to run this command:',
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

    ctx.bot.log.error(
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

    if check:
        view = ErrorView(check, ctx)
        view.message = await ctx.reply(
            embed=make_embed(title='Known error occured.', description='This is an already unknown error.', ctx=ctx),
            view=view,
        )
        return

    error_string = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    error_record = await ctx.bot.pool.fetchrow(
        """
            INSERT INTO
                Errors (
                    command,
                    user_id,
                    guild,
                    error,
                    full_error,
                    message_url,
                    occured_when,
                    fixed
                )
            VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
    """,
        ctx.command.qualified_name,
        ctx.author.id,
        ctx.guild.id if ctx.guild else None,
        str(error),
        ''.join(traceback.format_exception(type(error), error, error.__traceback__)),
        ctx.message.jump_url,
        datetime.datetime.now(tz=None),
        False,
    )
    if not error_record:
        msg = "Expected a Record but got None. This shouldn't happen"
        raise TypeError(msg)

    view = ErrorView(error_record, ctx)
    view.message = await ctx.reply(
        embed=make_embed(title='Unknown error occured', description='The developers have been informed.', ctx=ctx),
        view=view,
    )

    error_link = await ctx.bot.mystbin_cli.create_paste(
        files=(
            mystbin.File(
                filename=f'error{error_record['id']}.py',
                content=error_string,
            ),
        )
    )

    logger_embed = Embed(
        title=error.__class__.__name__,
        description=f"""```py\n{error_string}```""",
        colour=0xFFFFFF,
        url=error_link.url,
        ctx=ctx,
    )
    logger_embed.add_field(
        value=better_string(
            (
                f'- **ID:** {error_record['id']}',
                f'- **Command:** `{ctx.command.qualified_name}`',
                f'- **User:** {ctx.author}',
                f'- **Guild:** {ctx.guild or "No guild"}',
                f'- **URL: ** [Jump to message]({ctx.message.jump_url})',
                f'- **Occured: ** {discord.utils.format_dt(datetime.datetime.now(tz=None), "f")}',
            ),
            seperator='\n',
        )
    )
    await ctx.bot.logger_webhook.send(embed=logger_embed)

    return
