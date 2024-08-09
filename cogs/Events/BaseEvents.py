import contextlib
import inspect

import discord
from discord.ext import commands

from bot import Elysian
from utils.Embed import ElyEmbed


class DevEvents(commands.Cog):

    def __init__(self, bot: Elysian) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        assert self.bot.user is not None
        val = f"""

              Bot is on!\n
              Name     - {self.bot.user.name}\n
              Version  - {discord.__version__}\n
              ID       - {self.bot.user.id}\n
              """
        await self.bot.logger_webhook.send(
            embed=ElyEmbed(
                title="Bot started",
                description=str("```\n" + inspect.cleandoc(val) + "\n```"),
            )
        )

    @commands.Cog.listener("on_message_edit")
    async def edit_mechanic(self, before: discord.Message, after: discord.Message) -> None:
        if after.author.id == 688293803613880334:
            await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member | discord.User) -> None:
        if (
            self.bot.owner_ids
            and reaction.emoji
            and self.bot.user
            and user.id in self.bot.owner_ids
            and reaction.emoji == "🗑️"
            and reaction.message.author.id == self.bot.user.id
        ):
            with contextlib.suppress(discord.HTTPException):
                await reaction.message.delete()


async def setup(bot: Elysian) -> None:
    await bot.add_cog(DevEvents(bot))
