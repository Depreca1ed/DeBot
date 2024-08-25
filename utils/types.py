from typing import TypedDict

__all__ = ('BlackListedTypes', 'Image')


class BlackListedTypes(TypedDict):
    user: list[int]
    guild: list[int]


class Image(TypedDict):
    dominant_color: str | None
    image_id: str | int
    source: str | None
    url: str
