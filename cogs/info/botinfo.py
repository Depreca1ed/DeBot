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

if TYPE_CHECKING:
    from bot import Lagrange

from utils import OWNERS_ID, Embed, LagContext, better_string

try:
    from importlib.metadata import distribution, packages_distributions
except ImportError:
    from importlib_metadata import distribution, packages_distributions

import importlib


class BotInformation(commands.Cog):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name='about',
        aliases=['botinformation', 'boti', 'botinfo', 'info'],
        description='Get information about this bot',
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def botinfo(self, ctx: LagContext) -> None:
        bot = self.bot
        owners = [owner for owner in [bot.get_user(dev) for dev in OWNERS_ID] if owner]
        random_owner = random.choice(owners)
        embed = Embed(title=str(bot.user.name), description=bot.description, ctx=ctx)
        embed.set_author(
            name=f"Made by {' and '.join([dev.name for dev in owners]) }",
            icon_url=random_owner.avatar.url if random_owner.avatar else None,
        )
        embed.add_field(
            name='General Statistics',
            value=better_string(
                [
                    f'- **Servers :** `{len(bot.guilds)}`',
                    f'- **Users :** `{len(bot.users)}`',
                    f'  - **Installed by :** `{self.bot.appinfo.approximate_user_install_count}` users' 
                    if self.bot.appinfo.approximate_user_install_count
                    else None,
                ],
                seperator='\n',
            ),
        )

        distributions: list[str] = [
            dist
            for dist in packages_distributions()['discord']
            if any(file.parts == ('discord', '__init__.py') for file in distribution(dist).files)  # type: ignore[reportOptionalIterable]
        ]

        if distributions:
            dist_version = f'{distributions[0]} {importlib.metadata.version(distributions[0])}'
        else:
            dist_version = f'unknown {discord.__version__}'
        proc = psutil.Process()
        with proc.oneshot():
            memory = proc.memory_info().rss
            embed.add_field(
                name='System Statistics',
                value=better_string(
                    [
                        f'> Made in `Python {platform.python_version()}` using `{dist_version}`',
                        f'- **Uptime :** {humanize.naturaldelta(datetime.timedelta(seconds=datetime.datetime.now(datetime.UTC).timestamp() - bot.load_time.timestamp()))}',
                        f'- **Memory :** `{round((memory/1024)/1024)}/{round(((psutil.virtual_memory().total)/1024)/1024)} MB` (`{round(proc.memory_percent(), 2)}%`)',  # This is hardcoded to be in MB
                        f'- **CPU Usage :** `{proc.cpu_percent(interval=None)}`%',
                    ],
                    seperator='\n',
                ),
                inline=False,
            )

        embed.add_field(
            value=better_string(
                [
                    f'-# [Privacy Policy]({bot.appinfo.privacy_policy_url})' if bot.appinfo.privacy_policy_url else None,
                    f'-# [Terms of Service]({bot.appinfo.terms_of_service_url})'
                    if bot.appinfo.terms_of_service_url
                    else None,
                    f'[Invite the bot]({discord.utils.oauth_url(bot.user.id)})',
                    f'[Vote for {bot.user.name}]' if hasattr(bot, 'topgg_cli') else None,
                    '[Website](placeholder)' if hasattr(bot, 'website') else None,
                    f'[Support Server]({bot.invite_link})',
                ],
                seperator='\n',
            ),
        )

        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_image(url=bot.banner)

        await ctx.send(embed=embed)


async def setup(bot: Lagrange) -> None:
    await bot.add_cog(BotInformation(bot))
