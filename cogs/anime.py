from typing import List
import discord
from discord.ext import commands
import aiohttp
import json
import waifuim
import traceback
from utils import Embed


class SorPView(discord.ui.View):
    def __init__(self, ctx: commands.Context, message: discord.Message, req: str):
        super().__init__(timeout=500.0)
        self.ctx: commands.Context = ctx
        self.message: discord.Message = message
        self.smashers = []
        self.passers = []
        self.voted = []
        self.req: str = req

    @discord.ui.button(
        label='SMASH!',
        emoji='❤',
        style=discord.ButtonStyle.green,
    )
    async def smash(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.smashers.append(interaction.user)
        embed = interaction.message.embeds[0]
        self.voted.append(interaction.user.id)
        embed.description = f'<:elysia_yes:1187106328355803156> Smashers - {len(self.smashers)}\n<:elysia_no:1187109158785405058> Passers - {len(self.passers)}'
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(
        label='Pass...',
        emoji='🪑',
        style=discord.ButtonStyle.red,
    )
    async def passbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.passers.append(interaction.user)
        embed = interaction.message.embeds[0]
        self.voted.append(interaction.user.id)
        embed.description = f'<:elysia_yes:1187106328355803156> Smashers - {len(self.smashers)}\n<:elysia_no:1187109158785405058> Passers - {len(self.passers)}'
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji='🔁', style=discord.ButtonStyle.blurple)
    async def loopit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.passers: List = []
        self.smashers: List = []
        self.voted: List = []
        if self.req in ['neko', 'shinobu', 'megumin']:
            async with aiohttp.ClientSession() as session:
                waifufrfr = await session.get(f'https://api.waifu.pics/sfw/{self.req}')
                await session.close()
            waifulnk = json.loads(await waifufrfr.text())
            embed = Embed(
                title='Smash or Pass',
                description=f'<:elysia_yes:1187106328355803156> Smashers - {len(self.smashers)}\n<:elysia_no:1187109158785405058> Passers - {len(self.passers)}',
                ctx=self.ctx,
            )
            embed.set_image(url=str(waifulnk['url']))
            return await interaction.response.edit_message(embed=embed)
        elif self.req in ['waifu', 'maid', 'raiden']:
            embed = Embed(
                title='Smash or Pass',
                description=f'<:elysia_yes:1187106328355803156> Smashers - {len(self.smashers)}\n<:elysia_no:1187109158785405058> Passers - {len(self.passers)}',
                ctx=self.ctx,
            )
            cli = waifuim.WaifuAioClient()
            waifu = await cli.search(
                included_tags=[self.req],
                excluded_tags=[
                    'ass',
                    'hentai',
                    'milf',
                    'oral',
                    'paizuri',
                    'ecchi',
                    'ero',
                ],
                is_nsfw=False,
            )
            embed.set_image(url=str(waifu.url))
            embed.colour = discord.Colour.from_str(waifu.dominant_color)
            await cli.close()
            return await interaction.response.edit_message(embed=embed)
        return await interaction.response.send_message('Send this to dep and call him an idiot')

    async def interaction_check(self, interaction: discord.Interaction):
        if (
            interaction.user.id != self.ctx.author.id
            and interaction.data['custom_id'] == [x.custom_id for x in self.children][2]
        ):
            await interaction.response.send_message(
                'Only the command initiator can cycle through waifus in this message.',
                ephemeral=True,
            )
            return False
        if (
            interaction.user.id == self.ctx.author.id
            and interaction.data['custom_id'] == [x.custom_id for x in self.children][2]
        ):
            return True
        if (
            interaction.user.id == self.ctx.author.id
            and interaction.data['custom_id'] == [x.custom_id for x in self.children][0]
            and interaction.user.id in self.voted
        ):
            await interaction.response.send_message(
                embed=Embed(
                    title='Smashers',
                    description=', '.join([str(usr) for usr in self.smashers]),
                    ctx=self.ctx,
                ),
                ephemeral=True,
            )
            return False
        if (
            interaction.user.id == self.ctx.author.id
            and interaction.data['custom_id'] == [x.custom_id for x in self.children][1]
            and interaction.user.id in self.voted
        ):
            await interaction.response.send_message(
                embed=Embed(
                    title='Passers',
                    description=', '.join([str(usr) for usr in self.passers]),
                    ctx=self.ctx,
                ),
                ephemeral=True,
            )
            return False
        elif interaction.user.id not in self.voted:
            return True
        await interaction.response.send_message(
            'Once you choose a path, you cannot go back to it. Its your duty to choose one path and one path only. Its a one time chance. Thats how life works.',
            ephemeral=True,
        )
        return False

    async def on_timeout(self):
        await self.message.edit(view=None)
        self.stop()

    async def on_error(self, inter: discord.Interaction, error: Exception, item: discord.ui.Item):
        if inter.response.is_done():
            func = inter.followup.send
        else:
            func = inter.response.send_message
        errormsg = '```py\n' + ''.join(traceback.format_exception(type(error), error, error.__traceback__)) + '```'
        return await func(f'Error:\n{str(errormsg)}', ephemeral=False)


class Anime(commands.Cog):
    """All Anime related commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='waifu', description='Shows a picture of a...anime girl?')
    @commands.bot_has_permissions(external_emojis=True, embed_links=True, attach_files=True)
    async def waifu(self, ctx: commands.Context):
        """Shows a picture of a...anime girl?"""
        embed = Embed(
            ctx=ctx,
            title='Smash or Pass',
            description='<:elysia_yes:1187106328355803156> Smashers - 0\n<:elysia_no:1187109158785405058> Passers - 0',
        )
        cli = waifuim.WaifuAioClient()
        waifu = await cli.search(
            included_tags=['waifu'],
            excluded_tags=['ass', 'hentai', 'milf', 'oral', 'paizuri', 'ecchi', 'ero'],
            is_nsfw=False,
        )
        embed.set_image(url=str(waifu.url))
        embed.colour = discord.Colour.from_str(waifu.dominant_color)
        await cli.close()
        msg = await ctx.reply(embed=embed)
        view = SorPView(ctx, msg, 'waifu')
        return await msg.edit(view=view)


async def setup(bot):
    await bot.add_cog(Anime(bot))


# TODO(Depreca1ed): Rewrite this god awful code.
