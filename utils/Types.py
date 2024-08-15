from typing import TypedDict


class BlackListedTypes(TypedDict):
    user: list[int]
    guild: list[int]
