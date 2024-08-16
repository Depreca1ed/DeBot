from __future__ import annotations

import datetime
import importlib.metadata
import platform
import random
from typing import TYPE_CHECKING

import discord
import humanize
import psutil
from discord import app_commands
from discord.ext import commands
from jishaku.math import natural_size

from utils.config import OWNERS_ID

if TYPE_CHECKING:
    from bot import YukiSuou

from utils.Embed import YukiEmbed

try:
    from importlib.metadata import distribution, packages_distributions
except ImportError:
    from importlib_metadata import distribution, packages_distributions

import importlib


class BotInformation(commands.Cog):
    def __init__(self, bot: YukiSuou) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="about", aliases=["botinformation", "boti", "botinfo", "info"], description="Get information about this bot"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def botinfo(self, ctx: commands.Context[YukiSuou]) -> None:
        bot = self.bot
        owners = [owner for owner in [bot.get_user(dev) for dev in OWNERS_ID] if owner]
        random_owner = random.choice(owners)
        embed = YukiEmbed.default(ctx, title=str(bot.user.name), description=bot.description)
        embed.set_author(
            name=f"Made by {' and '.join([dev.name for dev in owners]) }",
            icon_url=random_owner.avatar.url if random_owner.avatar else None,
        )  # This f string is assuming you have 2 devs since originally down bad and Dep were the only one.
        visible_channels = list(bot.get_all_channels())
        bot_visible_statistics = [
            f"- **Servers :** `{len(bot.guilds)}`",
            f"- **Users :** `{len(bot.users)}`",
            f"- **Channels :** `{len(visible_channels)}`",
        ]
        embed.add_field(name="General Statistics", value="\n".join(bot_visible_statistics), inline=False)

        proc = psutil.Process()
        mem = proc.memory_full_info()
        distributions: list[str] = [
            dist
            for dist in packages_distributions()["discord"]
            if any(file.parts == ("discord", "__init__.py") for file in distribution(dist).files)  # type: ignore
        ]

        if distributions:
            dist_version = f"{distributions[0]} {importlib.metadata.version(distributions[0])}"
        else:
            dist_version = f"unknown {discord.__version__}"
        backend_statistic = [
            f"> Made in `Python {platform.python_version()}` & `{dist_version}`",
            f"- **Uptime :** {humanize.naturaldelta(datetime.timedelta(seconds=datetime.datetime.now().timestamp() - bot.load_time.timestamp()))}",
            f"- **Memory :** `{natural_size(mem.uss)}`",
            f"- **CPU :** `{proc.cpu_percent()}`%",
        ]
        embed.add_field(name="System Statistics", value="\n".join(backend_statistic), inline=False)

        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        await ctx.send(embed=embed)


async def setup(bot: YukiSuou) -> None:
    await bot.add_cog(BotInformation(bot))
