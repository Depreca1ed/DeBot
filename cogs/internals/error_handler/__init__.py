from __future__ import annotations

import difflib
import traceback
from typing import TYPE_CHECKING

import discord
import mystbin
from discord.ext import commands

from utils import BaseCog, DeContext, Embed, better_string

from .helpers import clean_error, generate_error_objects, make_embed
from .views import ErrorView, MissingArgumentHandler

if TYPE_CHECKING:
    import asyncpg

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


class ErrorHandler(BaseCog):
    def _find_closest_command(self, name: str) -> list[str]:
        return difflib.get_close_matches(
            name,
            [_command.name for _command in self.bot.commands],
            n=1,
        )

    def _format_tb(self, error: Exception) -> str:
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    async def _log_error(
        self,
        error: commands.CommandError,
        *,
        name: str,
        author: discord.User | discord.Member,
        message: discord.Message,
        guild: discord.Guild | None = None,
    ) -> asyncpg.Record:
        formatted_error = self._format_tb(error)
        time_occured = discord.utils.utcnow()

        record = await self.bot.pool.fetchrow(
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
            name,
            author.id,
            guild,
            str(error),
            formatted_error,
            message.jump_url,
            time_occured,
            False,
        )

        if not record:
            raise ValueError

        error_link = await self.bot.mystbin_cli.create_paste(
            files=(
                mystbin.File(
                    filename=f'error{record["id"]}.py',
                    content=formatted_error,
                ),
            )
        )

        logger_embed = Embed(
            title=error.__class__.__name__,
            description=f"""```py\n{formatted_error}```""",
            colour=0xFFFFFF,
            url=error_link.url,
        )

        logger_embed.add_field(
            value=better_string(
                (
                    f'- **ID:** {record["id"]}',
                    f'- **Command:** `{name}`',
                    f'- **User:** {author}',
                    f'- **Guild:** {guild.name if guild else "N/A"}',
                    f'- **URL: ** [Jump to message]({message.jump_url})',
                    f'- **Occured: ** {discord.utils.format_dt(time_occured, "f")}',
                ),
                seperator='\n',
            )
        )

        await self.bot.logger_webhook.send(embed=logger_embed)

        return record

    async def _is_known_error(
        self,
        error: commands.CommandError,
        *,
        command_name: str,
    ) -> asyncpg.Record | None:
        return await self.bot.pool.fetchrow(
            """
                SELECT
                    *
                FROM
                    Errors
                WHERE
                    command = $1
                    AND error = $2
                    AND fixed = $3
            """,
            command_name,
            str(error),
            False,
        )

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: DeContext, error: commands.CommandError) -> None | discord.Message:
        if (ctx.command and ctx.command.has_error_handler()) or (ctx.cog and ctx.cog.has_error_handler()):
            return None

        if not ctx.command:
            return None  # command will always exist

        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound) or not ctx.command:
            cmd = ctx.invoked_with
            if not cmd:
                return None

            possible_commands = self._find_closest_command(cmd)
            if possible_commands:
                embed = make_embed(
                    title='Command Not Found',
                    description=f'Could not find a command with that name. Perhaps you meant, `{possible_commands[0]}`?',
                    ctx=ctx,
                )

                await ctx.reply(embed=embed, delete_after=10.0)

            return None

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
            else:
                await ctx.reply(embed=embed)

            return None

        if isinstance(
            error,
            commands.MissingPermissions
            | commands.BotMissingPermissions
            | commands.MissingAnyRole
            | commands.MissingRole
            | commands.BotMissingAnyRole
            | commands.BotMissingRole,
        ):
            subject = (
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
                    f'{subject} missing the following {error_type_wording} to run this command:',
                    clean_error(final_iter, seperator='\n', prefix='- '),
                ),
                seperator='\n',
            )

            embed = make_embed(
                ctx=ctx,
                title=f'Missing {error_type_wording.title()}',
                description=content,
            )

            return await ctx.reply(embed=embed)

        if isinstance(error, defaults):
            return await ctx.reply(
                str(error),
                delete_after=getattr(error, 'retry_after', None),
            )

        ctx.bot.log.error(
            'Ignoring exception in running %s',
            ctx.command,
            exc_info=error,
        )

        known_error = await self._is_known_error(
            error,
            command_name=ctx.command.qualified_name,
        )

        if known_error:
            view = ErrorView(known_error, ctx)
            view.message = await ctx.reply(
                embed=make_embed(title='Known error occured.', description='This is an already unknown error.', ctx=ctx),
                view=view,
            )
        else:
            record = await self._log_error(
                error,
                name=ctx.command.qualified_name,
                author=ctx.author,
                message=ctx.message,
                guild=ctx.guild,
            )

            view = ErrorView(record, ctx)
            view.message = await ctx.reply(
                embed=make_embed(title='Unknown error occured', description='The developers have been informed.', ctx=ctx),
                view=view,
            )

        return None
