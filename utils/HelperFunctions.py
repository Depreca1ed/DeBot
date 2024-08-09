import datetime

import discord
import humanize
from discord.ext import commands

from bot import Elysian


async def DefaultToUser(ctx: commands.Context[Elysian]) -> discord.User | discord.Member:
    """Use this function with commands.parameter(default=DefaultToUser) only since its meant to be used for that"""
    return ctx.author


def StatusMessageGen(user: discord.Member) -> list[str]:
    activity_string: list[str] = []
    for activity in user.activities:
        if isinstance(activity, discord.BaseActivity):
            if isinstance(activity, discord.CustomActivity):
                if activity.name and activity.name != "Custom Status":
                    activity_string.append(activity.name)
            elif isinstance(activity, discord.Streaming):
                statement = ["Streaming"]
                if activity.game:
                    statement.append(f"[`{[activity.game]}`]")
                if activity.name:
                    if not activity.url:
                        statement.append(f"**{activity.name}**")
                    else:
                        statement.append(f"**[{activity.name}]({activity.url})**")
                if activity.platform:
                    statement.append(f"on `{activity.platform}`")
                if activity.twitch_name:
                    statement.append(f"as **{activity.twitch_name}**")
                if activity.created_at:
                    statement.append(
                        f"since **{humanize.naturaldelta(datetime.datetime.now().timestamp() - activity.created_at.timestamp())}**"
                    )
                activity_string.append(" ".join(statement))
            elif isinstance(activity, discord.Game):
                statement = [f"Playing **{activity.name}**"]
                if activity.platform:
                    statement.append(f"on `{activity.platform}`")
                if activity.created_at:
                    statement.append(
                        f"since **{humanize.naturaldelta(datetime.datetime.now().timestamp() - activity.created_at.timestamp())}**"
                    )
                activity_string.append(" ".join(statement))
            else:
                instance_datetime = activity.start or activity.created_at
                activity_string.append(
                    f"{activity.type.name.title()} **{f'[{activity.name}]({activity.url})' if activity.url else f'{activity.name}'}** {f'since **{humanize.naturaldelta(datetime.datetime.now().timestamp() - (instance_datetime.timestamp()))}**' if (instance_datetime) else ''}"
                )

        else:
            statement = ["Listening to **Spotify**"]
            statement.append(f"> **[{activity.title}]({activity.track_url})**")
            statement.append(f"> by **{','.join(activity.artists)}**")
            statement.append(f"> on **{activity.album}**")
            activity_string.append("\n".join(statement))
    return activity_string[:5]
