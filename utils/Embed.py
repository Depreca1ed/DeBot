from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord

from .config import DEV_THEME, OWNERS_ID, THEME_COLOUR

if TYPE_CHECKING:
    from collections.abc import Iterable

    from discord.ext import commands

    from bot import YukiSuou

__all__ = ("YukiEmbed",)


class YukiEmbed(discord.Embed):
    """Main purpose is to get the usual setup of Embed for a command or an error embed"""

    def __init__(
        self,
        colour: discord.Colour | int = discord.Colour.from_str(THEME_COLOUR),
        fields: Iterable[tuple[str, str]] = (),
        field_inline: bool = False,
        *,
        ctx: commands.Context[YukiSuou] | None = None,
        **kwargs: Any,
    ) -> None:
        if ctx:
            self.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url or None,
            )
            if ctx.author.id in OWNERS_ID:
                colour = discord.Colour.from_str(DEV_THEME)
        super().__init__(colour=colour, **kwargs)
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)
