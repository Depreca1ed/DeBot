from __future__ import annotations

import difflib

from discord.ext import commands

from utils import BaseCog, DeContext, better_string
from utils.embed import Embed

from .constants import ERROR_COLOUR, HANDLER_EMOJIS
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
)


class ErrorHandler(BaseCog):
    def clean_error(self, objects: list[str] | str, *, seperator: str, prefix: str) -> str:
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
                (prefix + f'{(perm.replace('_', ' ')).capitalize()}' for perm in objects),
                seperator=seperator,
            )
            if objects is not str
            else prefix + objects
        )

    def make_embed(self, *, title: str | None, description: str | None, ctx: DeContext | None = None) -> Embed:
        embed = Embed(title=title, description=description, ctx=ctx, colour=ERROR_COLOUR)
        embed.set_thumbnail(url=HANDLER_EMOJIS['MafuyuUnamused2'].url)
        return embed

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: DeContext, error: commands.CommandError) -> None:
        if (ctx.command and ctx.command.has_error_handler()) or (ctx.cog and ctx.cog.has_error_handler()):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound) or not ctx.command:
            cmd = ctx.invoked_with
            if not cmd:
                return

            cmd_list = [command.name for command in self.bot.commands]
            possible_cmd = difflib.get_close_matches(cmd, cmd_list, n=1)
            if possible_cmd:
                embed = self.make_embed(
                    title='Command Not Found',
                    description=f'Could not find a command with that name. Perhaps you meant, `{possible_cmd[0]}`?',
                    ctx=ctx,
                )
                await ctx.reply(embed=embed, delete_after=10.0)

            return

        if isinstance(error, commands.MissingRequiredArgument | commands.MissingRequiredAttachment):
            param_name = error.param.displayed_name or error.param.name
            embed = self.make_embed(
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
                if isinstance(error, commands.MissingPermissions | commands.MissingAnyRole | commands.MissingRole)
                else 'I'
            )
            error_type_wording = (
                'permissions' if isinstance(error, commands.MissingPermissions | commands.BotMissingPermissions) else 'roles'
            )
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
            final_iter = missing_roles or missing_role or missing_permissions
            if not final_iter:
                msg = 'Expected Not-None value'
                raise ValueError(msg)

            content = better_string(
                (
                    f'{person} are missing the following {error_type_wording} to run this command:',
                    self.clean_error(final_iter, seperator='\n', prefix='- '),
                ),
                seperator='\n',
            )

            embed = self.make_embed(
                ctx=ctx,
                title=f'Missing {error_type_wording.title()}',
                description=content,
            )
            await ctx.reply(embed=embed)
            return

        if type(error) in defaults:
            await ctx.reply(str(error), delete_after=getattr(error, 'retry_after', None))
