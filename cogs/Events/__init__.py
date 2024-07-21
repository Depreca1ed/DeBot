from bot import Elysian
from .Errors import Errors
from .BaseEvents import DevEvents


class Events(Errors, DevEvents, name="Events"):
    def __init__(self, bot: Elysian):
        self.bot = bot


async def setup(bot: Elysian):
    await bot.add_cog(Events(bot))
