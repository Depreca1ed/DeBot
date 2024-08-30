from datetime import datetime
from typing import Literal, TypedDict

__all__ = ('BlacklistBase', 'Image')


class BlacklistBase(TypedDict):
    reason: str
    lasts_until: datetime | None
    blacklist_type: Literal['guild', 'user']


class Image(TypedDict):
    dominant_color: str | None
    image_id: str | int
    source: str | None
    url: str
