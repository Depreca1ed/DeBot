from typing import TypedDict

__all__ = ('BlackListedTypes',)


class BlackListedTypes(TypedDict):
    user: list[int]
    guild: list[int]
