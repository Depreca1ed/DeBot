from __future__ import annotations

import contextlib
import datetime
import random
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from utils import BaseCog, Embed, better_string

if TYPE_CHECKING:
    from bot import DeBot
    from utils import DeContext

YOSHIMI_EMOJI = discord.PartialEmoji(name='YoshimiCreepy', animated=False, id=1277968074062168064)

READ_KITAKAWA = (
    "{role}!! Why haven't you read KitaKawa yet? You fool. You worthless human being.",
    '{role}! You must read KitaKawa',
    '{role}. According to raegan, you are not worth a dime unless you read kitakawa.',
    '{role} did you know reading kitakawa makes yourr life better?',
)


# Server here refers to the KitaKawa server.

# Warning to reviewers of this code, content after this may contain sensitive topics on some parts due to the nature of the one or more features.
# If this server doesn't involve you in any way, do not check this code or at least do not question the features. They are there as they were requested.
# Lastly, I will ban you if you cause trouble or I dont feel comfortable with you in the server. Thank you for reading this warning :D


class KitaKawa(BaseCog, name='KitaKawa'):
    def cog_load(self) -> None:
        self.mention_loop.start()
        self.venting_purge.start()

    def cog_unload(self) -> None:
        self.mention_loop.cancel()
        self.venting_purge.cancel()

    def cog_check(self, ctx: commands.Context[DeBot]) -> bool:
        return ctx.guild is not None and ctx.guild.id == self.guild.id

    @property
    def guild(self) -> discord.Guild:
        """Kitakawa server"""
        guild = self.bot.get_guild(1277813689092804650)
        assert guild is not None
        return guild

    @commands.Cog.listener('on_raw_reaction_add')
    async def yoshimi_filter(self, payload: discord.RawReactionActionEvent) -> None:
        ch = self.bot.get_channel(1277894451850776616)
        if (
            ch
            and ch.id == payload.channel_id
            and payload.event_type == 'REACTION_ADD'
            and payload.member
            and payload.emoji == YOSHIMI_EMOJI
            and payload.message_id == 1278029325765185588
        ):
            assert isinstance(ch, discord.TextChannel)
            with contextlib.suppress(discord.HTTPException):
                msg = await ch.fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, payload.member)
                await payload.member.send(
                    f'You were kicked from **{self.guild.name}** because you picked the `Yoshimi`\nYou can join back: discord.gg/J2BZD3ddRy',
                )
                await payload.member.kick(reason='[AUTOKICK] | They choose yoshimi role.')

    @tasks.loop(hours=4)
    async def mention_loop(self) -> None:
        ch = self.bot.get_channel(1277813689092804653)
        if not ch:
            return

        assert isinstance(ch, discord.TextChannel)
        role = self.guild.get_role(1295851367902089266)
        if not role or (role and not role.members):
            return
        content = random.choice(READ_KITAKAWA)
        content.replace('{role}', str(role))
        await ch.send(
            content,
            allowed_mentions=discord.AllowedMentions.all(),
        )

    @commands.command(name='readremind', help='[STAFF ONLY] Restart the mention cycle for kitakawa reminder')
    @commands.has_any_role(1277820252343894087)
    async def mention_loop_readreminder(self, ctx: DeContext) -> None:
        self.mention_loop.restart()
        with contextlib.suppress(discord.HTTPException):
            await ctx.message.add_reaction('<a:greentick:1297976474141200529>')

    @tasks.loop(time=datetime.time(hour=2, tzinfo=datetime.UTC))
    async def venting_purge(self) -> None:
        ch = self.bot.get_channel(1295861867754819715)
        if ch:
            assert isinstance(ch, discord.TextChannel)
            await ch.purge(limit=None)
            embed = Embed(
                title='Welcome to the venting channel.',
                description=(
                    'This is a safe space for anyone to talk about whatever may be troubling them. ',
                    "We're here for you! Please be respectful and mindful towards other members",
                    ', and always reach out to the [proper hotline](https://findahelpline.com/i/iasp) if needed. Thank you!!!',
                ),
                colour=0x000000,
            )
            embed.add_field(
                name='Few things to keep in mind',
                value=better_string(
                    (
                        '- This channel is strictly moderated therefore any form of misbehaviour will get you removed from this channel.',
                        "- Don't attempt to make jokes or be sarcastic during serious conversations. You are being insensitive by doing so.",
                        '- The messages in this channel will be purged completely everyday to maintain privacy of people who post their messages. ',
                    ),
                    seperator='\n',
                ),
            )
            if self.venting_purge.next_iteration is not None:
                embed.add_field(
                    value=f'Channel will be purged in {discord.utils.format_dt(self.venting_purge.next_iteration, "R")}.',
                )

            msg = await ch.send(embed=embed)
            await msg.pin()

    @commands.Cog.listener('on_message')
    async def ktkw_info(self, msg: discord.Message) -> None:
        if msg.guild and msg.guild.id != self.guild.id:
            return

        if 'airi where kitakawa' in msg.content:
            func = (
                msg.reference.resolved.reply
                if msg.reference and isinstance(msg.reference.resolved, discord.Message)
                else msg.reply
            )
            await func(
                content='https://mangadex.org/title/25632c2e-90d3-4a9f-9cfd-3132d52ca5ee/kitanai-kimi-ga-ichiban-kawaii',
            )


async def setup(bot: DeBot) -> None:
    await bot.add_cog(KitaKawa(bot))
