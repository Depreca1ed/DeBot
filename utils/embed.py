from __future__ import annotations

from typing import Any, Self

import discord

from . import THEME_COLOUR, DeContext

__all__ = ('Embed',)


class Embed(discord.Embed):
    """Main purpose is to get the usual setup of Embed for a command or an error embed."""

    def __init__(
        self,
        *,
        colour: discord.Colour | int | None = THEME_COLOUR,
        title: str | None = None,
        url: str | None = None,
        description: str | None = None,
        ctx: DeContext | None = None,
        **kwargs: Any,
    ) -> None:
        if ctx:
            self.set_footer(
                text=f'Requested by {ctx.author}',
                icon_url=ctx.author.display_avatar.url or None,
            )
        super().__init__(
            **kwargs,
        )
        super().__init__(
            colour=colour if colour and colour != discord.Colour.default() else THEME_COLOUR,
            title=title,
            url=url,
            description=description,
        )

    def add_field(self, *, name: str | None = '', value: str | None = '', inline: bool = False) -> Self:
        return super().add_field(name=name, value=value, inline=inline)
