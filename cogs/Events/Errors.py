import contextlib
import traceback
from typing import Any

import discord
import mystbin
from discord.ext import commands

from bot import Elysian
from utils.Checks import FeatureDisabled
from utils.Embed import ElyEmbed


def get_command_signature(context: commands.Context[Elysian], command: commands.Command[Any, ..., Any], /) -> str:
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
    parent: commands.Group[Any, ..., Any] | None = command.parent  # type: ignore
    entries: list[str] = []
    while parent is not None:
        if not parent.signature or parent.invoke_without_command:
            entries.append(parent.name)
        else:
            entries.append(parent.name + " " + parent.signature)
        parent = parent.parent  # type: ignore
    parent_sig = " ".join(reversed(entries))

    if len(command.aliases) > 0:
        aliases = "|".join(command.aliases)
        fmt = f"[{command.name}|{aliases}]"
        if parent_sig:
            fmt = parent_sig + " " + fmt
        alias = fmt
    else:
        alias = command.name if not parent_sig else parent_sig + " " + command.name

    return f"{context.clean_prefix}{alias} {command.signature}"


def clean_error_message(error_string: str) -> str:
    """This is a function used for cleaning the arguments of the errors like permissions, param names, etc."""
    new_error_string = error_string.replace("_", " ")
    new_error_string = new_error_string.capitalize()
    return new_error_string


class Errors(commands.Cog):
    def __init__(self, bot: Elysian) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context[Elysian], error: Exception) -> Any:
        if ctx.cog and commands.Cog._get_overridden_method(ctx.cog.cog_command_error):
            return

        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.CommandNotFound):
            if self.bot.owner_ids and ctx.author.id in self.bot.owner_ids:
                return
            with contextlib.suppress(discord.HTTPException):
                return await ctx.message.add_reaction("<:status_dnd:1237048172174643200>")
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"Command on cooldown! You can use this command after {error.retry_after:.2f} seconds.")
        if ctx.command is None:
            await self.bot.logger_webhook.send("Yup the assertion error triggered yet again less go")
        assert ctx.command is not None
        # Check for if bot has perms to send embeds since we need that, if it doesnt we will raise an error for the BotMissingPermissions. Unfortunately due to lack of programming knowledge I had to copy the text from that specified error and put my own shit here
        if (
            ctx.guild
            and [r for r in ctx.guild.me.roles if r]
            and ctx.channel.permissions_for(ctx.guild.me).embed_links is False
        ):
            permissions = "\n".join([f"- {clean_error_message('embed_links')}"])  # The string used in the command
            embed = ElyEmbed.default(
                ctx,
                title="<:redTick:1237048136527249510> | Missing Permissions",
                description=f"I am missing the following permissions to run this command.\n{permissions}",
                color=0xFF0000,
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
                embed=ElyEmbed.default(
                    ctx,
                    title="<:redTick:1237048136527249510> | Invalid Argument",
                    description=f"{error}",
                    color=0xFF0000,
                )
            )
        if isinstance(error, commands.TooManyArguments):
            return await ctx.send(
                embed=ElyEmbed.default(
                    ctx,
                    title="<:redTick:1237048136527249510> | Too Many Arguments",
                    description=f"{error}",
                    color=0xFF0000,
                )
            )
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                embed=ElyEmbed.default(
                    ctx,
                    title="<:redTick:1237048136527249510> | Missing argument",
                    description=f"You did not provide a {error.param.name} argument. \n- How to use the command:\n  - `{get_command_signature(ctx, ctx.command)}`",
                    color=0xFF0000,
                )
            )
        # Permission checks
        if isinstance(error, commands.MissingPermissions):
            permissions = "\n".join(
                [f"- {clean_error_message(permission)}" for permission in error.missing_permissions]
            )  # The string used in the command
            embed = ElyEmbed.default(
                ctx,
                title="<:redTick:1237048136527249510> | Missing Permissions",
                description=f"You are missing the following permissions to run this command.\n{permissions}",
                color=0xFF0000,
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
            permissions = "\n".join(
                [f"- {clean_error_message(permission)}" for permission in error.missing_permissions]
            )  # The string used in the command
            embed = ElyEmbed.default(
                ctx,
                title="<:redTick:1237048136527249510> | Missing Permissions",
                description=f"I am missing the following permissions to run this command.\n{permissions}",
                color=0xFF0000,
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

        ERROR_MESSAGES = {
            commands.NoPrivateMessage: "This command cannot be used in DMs",
            commands.NotOwner: "You cannot run this command. This command is reserved for the developers of the bot.",
            commands.UserInputError: "The input you have provided is invalid.",
            commands.NSFWChannelRequired: "This command can only be used in NSFW channels.",
            commands.PrivateMessageOnly: "This command can only be used in DMs.",
            FeatureDisabled: "This feature is not enabled in this server.",
        }
        message = ERROR_MESSAGES.get(type(error), None)  # type: ignore
        if message:
            await ctx.send(
                embed=ElyEmbed.default(
                    ctx,
                    title="<:status_dnd:1237048172174643200> | Cannot run command",
                    description=f"{message}",
                    color=0xFF0000,
                )
            )
        else:
            if isinstance(error, commands.CommandError):
                async with self.bot.pool.acquire() as conn:
                    check = await conn.fetchall(
                        "SELECT id from errorlogs WHERE command = ? AND error = ?",
                        (
                            ctx.command.qualified_name,
                            str(error),
                        ),
                    )
                    embed = ElyEmbed.default(
                        ctx,
                        title="Unknown error occured!",
                        description="The developers have been informed.",
                        color=0xFF0000,
                    )
                    if check:
                        embed.title = "Known error occured"
                        return await ctx.reply(embed=embed)
                    # Assuming we've informed the user WHEN the error is known
                    await ctx.reply(
                        embed=embed
                    )  # We inform them when its unknown except with no return since error channel must be informed yk yk
                    error_message = "".join(
                        traceback.format_exception(type(error), error, error.__traceback__)
                    )  # The traceback message, not to be sent in its purity to anything except the database
                    error_id = await conn.fetchone(
                        """INSERT INTO errorlogs (command, error, full_error, message) VALUES (?, ?, ?, ?) RETURNING id""",
                        (
                            str(ctx.command.qualified_name),
                            str(error),
                            str(error_message),
                            str(ctx.message.clean_content),
                        ),
                    )
                    await conn.commit()

                if len(error_message) >= 1990:
                    error_link = await self.bot.mystbin.create_paste(
                        files=[mystbin.File(filename="error.py", content=error_message)]
                    )

                    post_message = f"Error message was too long to be shown in this embed. \n- [Link to Error]({error_link})"
                else:
                    post_message = f"```py\n{error_message}```"
                error_embed = ElyEmbed.default(ctx, title=f"Error #{error_id[0]}", description=post_message, color=0x000000)
                extras = [
                    f"- **Command -** {ctx.command.qualified_name}",
                    f"- **Invoked as -** {ctx.message.clean_content}",
                    f"- **Short error**\n```py\n{error!s}```",
                ]
                error_embed.add_field(name="Extra", value="\n".join(extras), inline=False)
                return await self.bot.logger_webhook.send(embed=error_embed)


async def setup(bot: Elysian) -> None:
    await bot.add_cog(Errors(bot))
