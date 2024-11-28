from __future__ import annotations

import datetime
from io import BytesIO
from typing import TYPE_CHECKING

import discord
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

if TYPE_CHECKING:
    from bot import DeBot
    from utils import DeContext
from discord.ext import commands
from jishaku.functools import executor_function

from utils import BaseCog


@executor_function
async def spotify_img(activity: discord.Spotify, bot: DeBot, d):
    act = activity
    spim = Image.open(BytesIO(d)).resize((512,512))
    x=spim.resize((1,1)).getpixel((0,0))
    y=x
    x=list(x)
    x[0] = 255-x[0] if x[0]<255/2 else 255-(x[0]-round(255/2))
    x[1] = 255-x[1] if x[1]<255/2 else 255-(x[1]-round(255/2))
    x[2]= 255-x[2] if x[2]<255/2 else 255-(x[2]-round(255/2))
    x=tuple(x)
    im=Image.open(BytesIO(d)).resize((1024, 1024))
    e = ImageEnhance.Brightness(im)
    im = e.enhance(0.25)
    im = im.filter(ImageFilter.BLUR)
    im.paste(spim, (256, 256, 1024-256, 1024-256))
    fnt = ImageFont.truetype('assets/fonts/DejaVuSans-Bold.ttf', size=48)
    fntt = ImageFont.truetype('assets/fonts/DejaVuSans-Bold.ttf', size=32)
    dr=ImageDraw.Draw(im)
    dr.text((512, 1024-256+64), text=act.title , font=fnt, fill=x, anchor='mm')
    dr.text((512, 1024-256+128), text='By '+', '.join(act.artists), font=fntt, fill=x, anchor='mm')
    dr.text((512, 1024-256+192), text='On '+act.album, font=fntt, fill=x, anchor='mm')
    dr.rounded_rectangle((128-16,128-16, 1024-128+16, 128+16), fill=y, radius=45)
    val1 = (datetime.datetime.now(tz=datetime.UTC) - act.start)
    val2 = val1.seconds/act.duration.seconds
    dr.rounded_rectangle((128-16, 128-16, 128+16+round(val2*(1024-256)), 128+16), fill=x, radius=45)
    dr.text((128-16, 128+16+8), text=f'{round(val1.seconds/60)}:{val1.seconds%60}', fill=x, font=fntt, anchor='lt')
    dr.text((1024-128+16, 128+16+8), text=f'{round(act.duration.seconds/60)}:{act.duration.seconds%60}', fill=x, font=fntt, anchor='rt')
    buffer = BytesIO()
    im.save(buffer, 'png')
    buffer.seek(0)
    return buffer

class Spotify(BaseCog):
    @commands.command(name='spotify')
    async def spotify(self, ctx: DeContext, user: discord.Member=None) -> None:
        user = user or ctx.author
        act = [a for a in user.activities if isinstance(a, discord.Spotify)][0]
        actimg = await (await ctx.bot.session.get(act.album_cover_url)).read()
        x = await spotify_img(act, ctx.bot, actimg)
        await ctx.reply(file=discord.File(fp=x, filename="file.png"))
