from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import discord
import humanize

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


__all__ = ('ActivityHandler', 'better_string')


def better_string(data: Iterable[str | Any | None], *, seperator: str) -> str:
    return seperator.join(str(subdata) for subdata in data if subdata)


class ActivityHandler:
    def message_generate(self, activity: discord.BaseActivity | discord.Spotify) -> str:
        if isinstance(activity, discord.CustomActivity) and activity.name and activity != 'Custom Activity':
            return activity.name
        if isinstance(activity, discord.Streaming):
            return self.streaming(activity)
        if isinstance(activity, discord.Game):
            return self.game(activity)
        if isinstance(activity, discord.Spotify):
            return self.spotify(activity)
        return self.activity(activity)

    def streaming(self, activity: discord.Streaming) -> str:
        duration = (
            humanize.naturaldelta(datetime.datetime.now(datetime.UTC).timestamp() - activity.created_at.timestamp())
            if activity.created_at
            else None
        )
        return better_string(
            [
                'Streaming',
                f'`{[activity.game]}`' if activity.game else None,
                (
                    f'**[{activity.name}]({activity.url})**'
                    if activity.url
                    else f'**{activity.name}**'
                    if activity.name
                    else None
                ),
                f'on `{activity.platform}`' if activity.platform else None,
                f'as **{activity.twitch_name}**' if activity.twitch_name else None,
                (f'since **{duration}**' if duration else None),
            ],
            seperator=' ',
        )

    def game(self, activity: discord.Game) -> str:
        duration = (
            humanize.naturaldelta(datetime.datetime.now(datetime.UTC).timestamp() - activity.created_at.timestamp())
            if activity.created_at
            else None
        )
        return better_string(
            [
                f'Playing **{activity.name}**',
                f'on `{activity.platform}`' if activity.platform else None,
                (f'since **{duration}**' if duration else None),
            ],
            seperator=' ',
        )

    def spotify(self, activity: discord.Spotify) -> str:
        return better_string(
            [
                'Listening on **Spotify**',
                f'> **[{activity.title}]({activity.track_url})**',
                f"> by **{','.join(activity.artists)}**",
                f'> on **{activity.album}**',
            ],
            seperator='\n',
        )

    def activity(self, activity: discord.BaseActivity) -> str:
        if not isinstance(activity, discord.Activity):
            return 'Activity is not discord.Activity I guess???'  # NOTE: WHAT THE FUCK AM I SUPPOSED TO DO HERE?????
        instance_datetime = activity.start or activity.created_at
        duration = (
            humanize.naturaldelta(datetime.datetime.now(datetime.UTC).timestamp() - (instance_datetime.timestamp()))
            if instance_datetime
            else ''
        )
        return better_string(
            [
                f'{activity.type.name.title()}',
                (
                    f'**[{activity.name}]({activity.url})**'
                    if activity.url
                    else f'**{activity.name}**'
                    if activity.name
                    else None
                ),
                (duration),
            ],
            seperator=' ',
        )

    @classmethod
    def status_message_generator(cls, activities: Iterable[discord.BaseActivity | discord.Spotify]) -> Generator[str]:
        instance = cls()
        for activity in activities:
            yield instance.message_generate(activity)
