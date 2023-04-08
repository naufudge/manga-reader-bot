import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import List
from collections import deque
from async_kissmanga import Async_KissManga, no_cap_dict
import json, typing

intents = discord.Intents.all()

class ChapterPagination(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed], title: str):
        super().__init__(timeout=60)
        self._embeds = embeds
        self._queue = deque(embeds)
        self._initial = embeds[0]
        self._len = len(embeds)
        self._current_page = 1
        self._title = title
        self.children[0].disabled = True
        self._queue[0].set_footer(text=f"Page {self._current_page}/{self._len}")


    async def update_buttons(self, interaction: discord.Interaction, stop: int = None):
        for embed in self._queue:
            embed.set_footer(text=f"Page {self._current_page}/{self._len}")
        if self._current_page == self._len:
            self.children[2].disabled = True
        else:
            self.children[2].disabled = False
        if self._current_page == 1:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False
        if stop == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True
            self.children[2].disabled = True

        await interaction.message.edit(view=self)


    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.green)
    async def previousBtn(self, interaction: discord.Interaction, _):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page -= 1
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.red)
    async def stopBtn(self, interaction: discord.Interaction, _):
        embed = discord.Embed(title=f"Thank you for reading '__{self._title}__'" ,description=f"Please do read again! Thank you :)", color=0xfcffdc)
        self.stop()
        await self.update_buttons(interaction, stop=1)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.green)
    async def nextBtn(self, interaction: discord.Interaction, _):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self._current_page += 1
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=embed)

    async def on_timeout(self):
        timeout_embed = discord.Embed(title="Timeout!", description="Timed out since you took a while to switch pages. Thank you for reading!")
        # await self.interaction.response.edit_message(embed=timeout_embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial


def run_discord_bot():
    with open('config.json', 'r') as f:
        config = json.load(f)

    TOKEN = config['TOKEN'] #Miku Bot Token
    client = commands.Bot(command_prefix='m!', intents=intents, help_command=None)

    # Repeats what you say
    @client.command()
    async def say(ctx, *, msg):
        await ctx.message.delete()
        await ctx.channel.send(msg)

    @client.command(name="manga")
    async def manga(ctx, manga_name, chapter):
        km = Async_KissManga()
        # km = KissManga()
        search = await km.Search(manga_name)
        try:
            exact_search = no_cap_dict(search)[manga_name.lower()]
        except KeyError:
            await ctx.channel.send(f"Could not find a manga for '___{manga_name}___' :(")
            list_of_results = list(search.keys())
            # results = ', '.join(list_of_results)
            if list_of_results != None:
                temp_results = sorted(list_of_results)[0:15]
                await ctx.channel.send("**Did you mean any of the titles below?**")
                await ctx.channel.send('\n'.join(temp_results))
            else:
                await ctx.channel.send("No results found :/")
            return

        chapters = km.Chapters(exact_search)
        try:
            chap_link = chapters[int(chapter)-1][1]
        except IndexError:
            await ctx.channel.send(f"Chapter {chapter} not found :(")
            return

        # PAGINATION BELOW
        pages = km.read_chap(chap_link)
        page_embeds = []
        for each_page in pages:
            page_embed = discord.Embed(title=f"{chapters[int(chapter)-1][0]}", description=f"Page {pages.index(each_page)+1}/{len(pages)+1}", color=0xfcffdc)
            page_embed.set_image(url=each_page)
            page_embeds.append(page_embed)
        buttons = [u"\u23EA", u"\u2B05", u"\U0001F6AB", u"\u27A1", u"\u23E9"] # skip to start, left, stop, right, skip to end
        current_page = 0
        msg = await ctx.channel.send(embed=page_embeds[current_page])

        for button in buttons:
            await msg.add_reaction(button)

        while True:
            try:
                reaction, user = await client.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)

            except asyncio.TimeoutError:
                print("Timeout")
                return

            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 0

                elif reaction.emoji == u"\u2B05":
                    if current_page > 0:
                        current_page -= 1

                elif reaction.emoji == u"\u27A1":
                    if current_page < len(pages)-1:
                        current_page += 1

                elif reaction.emoji == u"\u23E9":
                    current_page = len(pages)-1

                elif reaction.emoji == u"\U0001F6AB":
                    finish_embed = discord.Embed(title=f"Thank you for reading '__{chapters[int(chapter)-1][0]}__'" ,description=f"Please do continue reading :) Thank you!", color=0xfcffdc)
                    await msg.edit(embed=finish_embed)
                    return

                for button in buttons:
                    await msg.remove_reaction(button, ctx.author)

                if current_page != previous_page:
                    await msg.edit(embed=page_embeds[current_page])


    @client.tree.command(name="help", description="Get help on how to use the bot")
    @app_commands.describe(command="If there's a specific command you need help with type here")
    async def nau_help(interaction: discord.Interaction, command: typing.Optional[str]):
        help_embed = discord.Embed(title="__Help__", color=0x974dae ,description="Find all the supported slash commands of this bot below. If you want more information on specific commands, use: ``/help command: <name of command>``\n")
        help_embed.add_field(name="``/manga <name of manga> <chapter number>``", value="Start reading any manga that is available in the kissmanga database!", inline=False)
        help_embed.add_field(name="``/manga_search <name of manga>``", value="Lookup any manga that you're looking for and check if it's available", inline=False)
        await interaction.response.send_message(embed=help_embed)


    @client.tree.command(name="manga")
    @app_commands.describe(manga_name="What's the name of the manga you want?")
    @app_commands.describe(chapter="Which chapter of the manga would you like to read?")
    async def manga_slash(interaction: discord.Interaction, manga_name: str, chapter: int):
        km = Async_KissManga()
        await interaction.response.defer()
        search = await km.Search(manga_name)
        try:
            exact_search = no_cap_dict(search)[manga_name.lower()]
        except KeyError:
            await interaction.followup.send(f"Could not find a manga for '___{manga_name}___' :(")
            list_of_results = list(search.keys())
            # results = ', '.join(list_of_results)
            if list_of_results != None:
                temp_results = sorted(list_of_results)[0:15]
                temp_results = '\n'.join(temp_results)
                await interaction.followup.send(f"**Did you mean any of the titles below?**\n{temp_results}")
            else:
                await interaction.followup.send("No results found :/")
            return

        chapters = km.Chapters(exact_search)
        try:
            chap_link = chapters[int(chapter)-1][1]
            chap_title = chapters[int(chapter)-1][0]
        except IndexError:
            await interaction.followup.send(f"Chapter {chapter} not found :(")
            return

        # PAGINATION BELOW
        pages = km.read_chap(chap_link)
        page_embeds = []
        for each_page in pages:
            page_embed = discord.Embed(title=f"__{chap_title}__", color=0xfcffdc)
            page_embed.set_image(url=each_page)
            page_embeds.append(page_embed)
        view = ChapterPagination(page_embeds, chap_title)
        await interaction.followup.send(embed=view.initial, view=view)


    # Async searching below
    @client.tree.command(name="manga_search")
    @app_commands.describe(manga_name="What's the name of the manga you want?")
    async def manga_search(interaction: discord.Interaction, manga_name: str):
        km = Async_KissManga()
        await interaction.response.defer()
        searches = await km.Search(manga_name)
        searches = list(searches.keys())

        list_of_results = [f'**Your search for __{manga_name}__ returned the folowing:**']
        list_of_results += sorted(searches)
        if list_of_results != None:
            temp_results = list_of_results[0:20]
            await interaction.followup.send('\n'.join(temp_results))
        else:
            await interaction.followup.send("No results found :/")


    # SYNCHRONOUS MANGA SEARCHING BELOW
    # @client.tree.command(name="manga_search")
    # @app_commands.describe(manga_name="What's the name of the manga you want?")
    # async def manga(interaction: discord.Interaction, manga_name: str):
    #     km = KissManga()
    #     await interaction.response.defer()
    #     start_time = time.time()
    #     searches = list(km.Search(manga_name).keys())

    #     list_of_results = [f'**Your search for __{manga_name}__ returned the folowing:**']
    #     list_of_results += searches
    #     if list_of_results != None:
    #         temp_results = list_of_results[0:20]
    #         await interaction.followup.send('\n'.join(temp_results))
    #         print(f"took {time.time() - start_time} seconds")
    #     else:
    #         await interaction.followup.send("No results found :/")


    @client.event
    async def on_ready():
        print(f'{client.user.name} has connected to Discord!')

        try:
            synced = await client.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

        status = discord.Status.idle
        await client.change_presence(activity=discord.Game(name="a melody ♡"), status=status)

    client.run(TOKEN)
