from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import DeBot  # noqa: F401

__all__ = ('DeContext',)


class DeContext(commands.Context['DeBot']):
    @discord.utils.copy_doc(commands.Context['DeBot'].reply)
    async def reply(self, content: str | None = None, **kwargs: Any) -> discord.Message:
        try:
            return await super().reply(content=content, **kwargs)
        except discord.HTTPException:
            return await super().send(content=content, **kwargs)
