from __future__ import annotations

import datetime
import importlib.metadata
import platform

import discord
import humanize
import psutil
from discord import app_commands
from discord.ext import commands

from utils import BaseCog, Context, Embed, better_string

try:
    from importlib.metadata import distribution, packages_distributions
except ImportError:
    from importlib_metadata import distribution, packages_distributions

import importlib


class BotInformation(BaseCog):
    @commands.hybrid_command(
        name='about',
        aliases=['info'],
        help='Get information about this bot',
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def botinfo(self, ctx: Context) -> None:
        bot = self.bot
        embed = Embed(title=str(bot.user.name), description=bot.description, ctx=ctx)
        embed.set_author(
            name=f'Made by {bot.appinfo.owner}',
            icon_url=bot.appinfo.owner.display_avatar.url,
        )
        embed.add_field(
            name='General Statistics',
            value=better_string(
                [
                    f'- **Servers :** `{len(bot.guilds)}`',
                    f'- **Users :** `{len(bot.users)}`',
                    (
                        f'  - **Installed by :** `{self.bot.appinfo.approximate_user_install_count}` users'
                        if self.bot.appinfo.approximate_user_install_count
                        else None
                    ),
                ],
                seperator='\n',
            ),
        )

        distributions: list[str] = [
            dist
            for dist in packages_distributions()['discord']
            if any(file.parts == ('discord', '__init__.py') for file in distribution(dist).files)  # pyright: ignore[reportOptionalIterable]
        ]

        if distributions:
            dist_version = f'{distributions[0]} {importlib.metadata.version(distributions[0])}'
        else:
            dist_version = f'unknown {discord.__version__}'
        proc = psutil.Process()
        with proc.oneshot():
            memory = proc.memory_info().rss
            uptime = humanize.naturaldelta(
                datetime.timedelta(seconds=datetime.datetime.now(datetime.UTC).timestamp() - bot.start_time.timestamp())
            )
            memory_usage = (
                str(round((memory / 1024) / 1024))
                + '/'
                + str(round(((psutil.virtual_memory().total) / 1024) / 1024))
                + ' MB'
            )
            embed.add_field(
                name='System Statistics',
                value=better_string(
                    [
                        f'> Made in `Python {platform.python_version()}` using `{dist_version}`',
                        f'- **Uptime :** {uptime}',
                        f'- **Memory :** `{memory_usage}` (`{round(proc.memory_percent(), 2)}%`)',
                    ],
                    seperator='\n',
                ),
                inline=False,
            )

        embed.add_field(
            value=better_string(
                [
                    (
                        (
                            f'-# [Privacy Policy]({bot.appinfo.privacy_policy_url})\n'
                            f'-# [Terms of Service]({bot.appinfo.terms_of_service_url})'
                        )
                        if bot.appinfo.terms_of_service_url and bot.appinfo.privacy_policy_url
                        else None
                    ),
                    '-# [Invite the bot](https://discord.com/oauth2/authorize?client_id=1260312970890842182)',
                    '-# [Support Server](https://discord.gg/mtWF6sWMex)',
                ],
                seperator='\n',
            ),
        )

        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_image(url=(bot.user.banner or (await bot.fetch_user(bot.user.id)).banner))

        await ctx.send(embed=embed)
