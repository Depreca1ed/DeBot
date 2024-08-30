from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Lagrange

from .command_errors import CommandErrors


class Errors(CommandErrors, name='Errors'):
    def __init__(self, bot: Lagrange) -> None:
        self.bot = bot
