from __future__ import annotations

import datetime
import difflib
import operator
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, menus

from utils import BaseCog, DeContext, DePaginator, Embed, WaifuNotFoundError, better_string

from .constants import HANDLER_EMOJIS
from .helpers import clean_error, generate_error_objects, logger_embed, make_embed
from .views import ErrorView, MissingArgumentHandler

if TYPE_CHECKING:
    import asyncpg

    from bot import DeBot

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
    WaifuNotFoundError,
)


class ErrorPageSource(menus.ListPageSource):
    def __init__(self, bot: DeBot, entries: list[asyncpg.Record]) -> None:
        self.bot = bot
        entries = sorted(entries, key=operator.itemgetter('id'))
        super().__init__(entries, per_page=1)

    async def format_page(self, _: DePaginator, entry: asyncpg.Record) -> Embed:
        embed = await logger_embed(self.bot, entry)
        embed.title = embed.title + f'/{self.get_max_pages()}' if embed.title else None
        return embed


class ErrorHandler(BaseCog):
    def _find_closest_command(self, name: str) -> list[str]:
        return difflib.get_close_matches(
            name,
            [_command.name for _command in self.bot.commands],
            n=1,
        )

    def _format_tb(self, error: Exception) -> str:
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__)).replace(
            str(Path.cwd()), f'/{self.bot.user.name}'
        )

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
        time_occured = datetime.datetime.now()

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
            guild.id if guild else None,
            str(error),
            formatted_error,
            message.jump_url,
            time_occured,
            False,
        )

        if not record:
            raise ValueError

        embed = await logger_embed(self.bot, record)

        await self.bot.logger_webhook.send(embed=embed)

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
            embed = make_embed(
                title='Command failed',
                description=str(error),
                ctx=ctx,
            )
            return await ctx.reply(
                delete_after=getattr(error, 'retry_after', None),
                embed=embed,
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
                embed=make_embed(
                    title='Known error occured.', description='This is a known error, and is yet to be fixed.', ctx=ctx
                ),
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

    @commands.group(
        name='error',
        description='Handles all things related to error handler logging.',
        hidden=True,
        invoke_without_command=True,
    )
    async def errorcmd_base(self, ctx: DeContext) -> None:
        await ctx.send_help(ctx.command)

    @errorcmd_base.command(name='show', description='Shows the embed for a certain error')
    async def error_show(self, ctx: DeContext, error_id: int | None = None) -> None:
        if error_id:
            error_record = await self.bot.pool.fetchrow("""SELECT * FROM Errors WHERE id = $1""", error_id)
            if not error_record:
                await ctx.reply('Error not found.')
                return
            embed = await logger_embed(self.bot, error_record)
            await ctx.reply(embed=embed)
            return
        errors = await self.bot.pool.fetch(
            """SELECT * FROM Errors""",
        )
        paginate = DePaginator(ErrorPageSource(self.bot, errors), ctx=ctx)
        await paginate.start()

    @errorcmd_base.command(name='fix', description='Mark an error as fixed')
    async def error_fix(self, ctx: DeContext, error_id: int) -> None:
        data = await self.bot.pool.fetchrow("""SELECT * FROM Errors WHERE id = $1""", error_id)
        if not data:
            await ctx.reply(f'Cannot find an error with the ID: `{error_id}`')
            return
        await self.bot.pool.execute("""UPDATE Errors SET fixed = $1 WHERE id = $2""", True, error_id)
        notifiers = await self.bot.pool.fetch("""SELECT user_id FROM ErrorReminders WHERE id = $1""", error_id)
        if notifiers:
            users = [_ for _ in [self.bot.get_user(user['user_id']) for user in notifiers] if _]
            for user in users:
                try:
                    await user.send(f"Hey! Error `#{data['id']}` in the `{data['command']}` command has been fixed.")
                except discord.errors.Forbidden:
                    continue
            # Assuming all goes fine
            await self.bot.pool.execute("""DELETE FROM ErrorReminders WHERE id = $1""", error_id)
        await ctx.message.add_reaction(str(HANDLER_EMOJIS['greentick']))
