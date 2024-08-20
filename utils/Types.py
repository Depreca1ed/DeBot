from enum import IntEnum, StrEnum
from typing import TypedDict

__all__ = ('BlackListedTypes', 'ModerationFlags', 'ModerationThresholds')


class BlackListedTypes(TypedDict):
    user: list[int]
    guild: list[int]


class ModerationFlags(StrEnum):
    NEW_ACCOUNT = 'Suspicious Member: Account age less than or equal to 14 days'


class ModerationThresholds(IntEnum):
    NEW_ACCOUNT = 14


# TODO(Depreca1ed): Possibly implement this better?
