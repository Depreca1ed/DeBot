from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import discord

from .config import THEME_COLOUR

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .context import DeContext

__all__ = ('Embed',)


class Embed(discord.Embed):
    """Main purpose is to get the usual setup of Embed for a command or an error embed"""

    def __init__(
        self,
        colour: discord.Colour | int | None = THEME_COLOUR,
        fields: Iterable[tuple[str, str]] = (),
        *,
        field_inline: bool = False,
        ctx: DeContext | None = None,
        **kwargs: Any,
    ) -> None:
        if ctx:
            self.set_footer(
                text=f'Requested by {ctx.author}',
                icon_url=ctx.author.display_avatar.url or None,
            )
        super().__init__(colour=colour if colour != discord.Colour.default() else THEME_COLOUR, **kwargs)
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)

    def add_field(self, *, name: str | None = '', value: str | None = '', inline: bool = False) -> Self:
        return super().add_field(name=name, value=value, inline=inline)
