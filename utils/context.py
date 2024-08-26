from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Lagrange  # noqa: F401

__all__ = ('LagContext',)


class LagContext(commands.Context['Lagrange']):
    @discord.utils.copy_doc(commands.Context['Lagrange'].reply)
    async def reply(self, content: str | None = None, **kwargs: Any) -> discord.Message:
        try:
            return await super().reply(content=content, **kwargs)
        except discord.HTTPException:
            return await super().send(content=content, **kwargs)
