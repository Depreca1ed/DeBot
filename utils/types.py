from datetime import datetime
from typing import TypedDict

__all__ = ('BlackListedTypes', 'Image')


class BlacklistBase(TypedDict):
    snowflake: int
    reason: str
    lasts_until: datetime | None


class BlackListedTypes(TypedDict):
    user: list[BlacklistBase]
    guild: list[BlacklistBase]


class Image(TypedDict):
    dominant_color: str | None
    image_id: str | int
    source: str | None
    url: str
