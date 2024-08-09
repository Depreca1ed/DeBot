from bot import Elysian

from .BaseEvents import DevEvents
from .Errors import Errors
from .Wordism import Wordism


class Events(Errors, DevEvents, Wordism, name="Events"):
    def __init__(self, bot: Elysian) -> None:
        self.bot = bot


async def setup(bot: Elysian) -> None:
    await bot.add_cog(Events(bot))
