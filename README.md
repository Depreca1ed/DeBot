DeBot
=========
DeBot!

Where can I use the bot & How can I host it?
============================================
You can use it in the support server. Unfortunately you need to put in effort and find the link to it in the code. 

As for how you can host it:
- [Clone the repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
- Create a config.py file in the `utils` directory and add the following values
```py
import discord

__all__ = (
    'BASE_PREFIX',
    'BOT_TOKEN',
    'OWNERS_ID',
    'POSTGRES_CREDENTIALS',
    'THEME_COLOUR',
    'WEBHOOK_URL',
    'WAIFU_TOKEN',
    'SERVER_INVITE',
    'DESCRIPTION',
)

BASE_PREFIX = '' # The base prefix of the bot, which will be converted to multiple cases of itself if applicable.

BOT_TOKEN = '' # The discord bot token

WAIFU_TOKEN = '' # The https://www.waifu.im/ token. If you don't wish to use it, please do make neccessary changes in cogs/anime.py if applicable

OWNERS_ID = [] # Discord user IDs of the owners, this is same as commands.Bot.owner_ids


DESCRIPTION = '' # The really long description of the bot.


POSTGRES_CREDENTIALS = {
    'user': '',
    'password': '',
    'database': '',
    'host': '',
    'port': 5432,
} # The postgres credentials for the bot's database

THEME_COLOUR = discord.Colour.random() # The colour used in most of the embeds of the bot, as an example its set to random but you can change it to anything you prefer.


WEBHOOK_URL = '' # The link to the webhook you wish for the bot to send all its private logging messages to, 
```
> Yes I tend to put everything which feels even slightly similar to being a constant value in a config.py file. Just something I prefer to be more comfortable with I suppose

- After setting up all of the above, you can run the bot by running the `__main__.py` file. 

If you are collaborating...
===========================
Run the below after installing the dependencies to activate auto-formatting pre-commit hooks:
```sh
pre-commit install
```

- After setting up all of the above, you can run the bot by running the `__main__.py` file.
