import discord
from discord.ext import commands

from bot import Elysian
from typing import cast


class Wordism(commands.Cog):

    def __init__(self, bot: Elysian):
        self.bot = bot

    @commands.Cog.listener("on_member_join")
    async def welcome_event(self, member: discord.Member):
        ch = self.bot.guild.get_channel(1262409199992705105)
        assert ch is not None
        ch = cast(discord.TextChannel, ch)
        await ch.send(content=f"**{member.name}** just joined the server. They are from **placeholder**")


async def setup(bot: Elysian):
    await bot.add_cog(Wordism(bot))
