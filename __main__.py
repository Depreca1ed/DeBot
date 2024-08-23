"""This file was sourced from [RoboDanny](https://github.com/Rapptz/RoboDanny).

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Any

import discord

from bot import YukiSuou

if TYPE_CHECKING:
    from collections.abc import Generator


class RemoveNoise(logging.Filter):
    def __init__(self) -> None:
        super().__init__(name='discord.state')

    def filter(self, record: logging.LogRecord) -> bool:
        return not (record.levelname == 'WARNING' and 'referencing an unknown' in record.msg)


@contextlib.contextmanager
def setup_logging() -> Generator[Any, Any, Any]:
    log: logging.Logger = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(filename='YukiSuou.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=5)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)
        yield

    finally:
        # __exit__
        handlers: list[logging.Handler] = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


if __name__ == '__main__':
    with setup_logging():

        async def run_bot() -> None:
            async with YukiSuou() as bot:
                await bot.start(bot.token)
        asyncio.run(run_bot())
