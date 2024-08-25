from typing import TypedDict

__all__ = ('BlackListedTypes', 'WaifuImImage', 'WaifuIm')


class BlackListedTypes(TypedDict):
    user: list[int]
    guild: list[int]


class WaifuImImage(TypedDict):
    dominant_color: str
    image_id: int
    is_nsfw: bool
    source: str | None
    url: str


class WaifuIm(TypedDict):
    images: list[WaifuImImage]
