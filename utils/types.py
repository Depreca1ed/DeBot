from typing import TypedDict

__all__ = ('BlackListedTypes', 'WaifuImage', 'Waifu')


class BlackListedTypes(TypedDict):
    user: list[int]
    guild: list[int]


class WaifuImage(TypedDict):
    dominant_color: str
    image_id: int
    is_nsfw: bool
    source: str | None
    url: str


class Waifu(TypedDict):
    images: list[WaifuImage]
