from datetime import datetime
import io
import json
import random
import typing

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType


class ConfirmOrDeny(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=180)
        self.add_item(
            item=discord.ui.Button(
                label="Sent from {0}".format(guild.name),
                disabled=True,
                style=discord.ButtonStyle.success,
            )
        )


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name="obama", description="Returns video of obama saying specified phrase"
    )
    @discord.option(name="message", type=str, description="Phrase for Obama to say.")
    @commands.cooldown(1, 5, BucketType.member)
    async def obama(self, ctx: discord.ApplicationContext, *, message: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://talkobamato.me",
                data=aiohttp.FormData(({"input_text": message})),
            ) as request:
                print(request.url.query.get("speech_key"))
                async with session.get(
                    "http://www.talkobamato.me/synth/output/{}/obama.mp4".format(
                        request.url.query.get("speech_key")
                    ),
                    timeout=None,
                ) as video:
                    await ctx.respond(
                        file=discord.File(
                            io.BytesIO(await video.read()), filename="Ross.mp4"
                        )
                    )
        await session.close()

    @discord.slash_command(
        name="textart", description="Create text art from a word/phrase"
    )
    @discord.option(name="text", type=str, description="Text to be manipulated")
    @commands.cooldown(1, 10, BucketType.member)
    async def textart(self, ctx: discord.ApplicationContext, *, text: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://artii.herokuapp.com/make?text={0}".format(text)
            ) as response:
                await ctx.respond(str("```\n" + (await response.text()) + "```"))
            await session.close()

    @discord.slash_command(name="shiba", description="Get picture of random shiba.")
    @commands.cooldown(1, 5, BucketType.member)
    async def shiba(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true"
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), title="Random Shiba"
                    ).set_image(url=jobj[0])
                )
            await session.close()

    @discord.slash_command(name="fox", description="Get picture of random fox.")
    @commands.cooldown(1, 5, BucketType.member)
    async def fox(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomfox.ca/floof/") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), title="Random Fox"
                    ).set_image(url=jobj.get("image"))
                )
            await session.close()

    @discord.slash_command(name="dog", description="Get picture of random dog.")
    @commands.cooldown(1, 5, BucketType.member)
    async def dog(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://dog.ceo/api/breeds/image/random"
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), title="Random Dog"
                    ).set_image(url=jobj.get("message"))
                )
            await session.close()

    @discord.slash_command(name="cat", description="Get picture of random cat.")
    @commands.cooldown(1, 5, BucketType.member)
    async def cat(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://aws.random.cat/meow") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), title="Random Cat"
                    ).set_image(url=jobj.get("file"))
                )
            await session.close()

    @discord.slash_command(name="insult", description="Get a random insult.")
    @commands.cooldown(1, 5, BucketType.member)
    async def insult(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://evilinsult.com/generate_insult.php?type=json&lang=en"
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), description=jobj.get("insult")
                    ).set_footer(text="Just kidding.. maybe...")
                )
            await session.close()

    @discord.slash_command(name="dadjoke", description="Get a random dad joke.")
    @commands.cooldown(1, 5, BucketType.member)
    async def dadjoke(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://icanhazdadjoke.com/", headers={"Accept": "application/json"}
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        title="Random Dad Joke",
                        description=jobj.get("joke"),
                    )
                )
            await session.close()

    @discord.slash_command(
        name="chucknorris", description="Get a random Chuck Norris joke."
    )
    @commands.cooldown(1, 5, BucketType.member)
    async def chuck(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.chucknorris.io/jokes/random"
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        title="Random Chuck Norris Joke",
                        description=jobj.get("value"),
                    )
                )
            await session.close()

    @discord.slash_command(
        name="kanyequote", description="Get a random Kanye West quote."
    )
    @commands.cooldown(1, 5, BucketType.member)
    async def kanye(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.kanye.rest/") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        title="Random Kanye West Quote",
                        description=f"> \"{jobj.get('quote')}\" - Kanye West",
                    )
                )
            await session.close()

    @discord.slash_command(name="advice", description="Get a random piece of advice.")
    @commands.cooldown(1, 5, BucketType.member)
    async def advice(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.adviceslip.com/advice") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        title="Random Piece of Advice",
                        description=jobj.get("slip").get("advice"),
                    )
                )
            await session.close()

    @discord.slash_command(
        name="aicat", description="Get picture of random AI generated cat."
    )
    @commands.cooldown(1, 5, BucketType.member)
    async def aicat(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://thiscatdoesnotexist.com/") as response:
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        title="Random AI Generated Cat",
                    ).set_image(url="attachment://cat.jpg"),
                    file=discord.File(
                        fp=io.BytesIO(await response.read()), filename="cat.jpg"
                    ),
                )
            await session.close()

    @discord.slash_command(
        name="yomomma", description="Generates a random Yo momma joke."
    )
    @commands.cooldown(1, 5, BucketType.member)
    async def yomomma(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.yomomma.info/") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), description=jobj.get("joke")
                    )
                )
            await session.close()

    @discord.slash_command(name="bunny", description="Get a random Bunny gif.")
    @commands.cooldown(1, 5, BucketType.member)
    async def bunny(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.bunnies.io/v2/loop/random/?media=gif"
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        title="Random Bunny", color=discord.Color.dark_grey()
                    ).set_image(url=(jobj.get("media").get("gif")))
                )
            await session.close()

    @discord.slash_command(name="duck", description="Get a random Duck gif.")
    @commands.cooldown(1, 5, BucketType.member)
    async def duck(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://random-d.uk/api/v1/random?type=gif"
            ) as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        title="Random Duck", color=discord.Color.dark_grey()
                    ).set_image(url=(jobj.get("url")))
                )
            await session.close()

    @discord.slash_command(name="koala", description="Get a random Koala pic.")
    @commands.cooldown(1, 5, BucketType.member)
    async def koala(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/img/koala") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        title="Random Koala", color=discord.Color.dark_grey()
                    ).set_image(url=(jobj.get("link")))
                )
            await session.close()

    @discord.slash_command(name="panda", description="Get a random Panda pic.")
    @commands.cooldown(1, 5, BucketType.member)
    async def panda(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/img/panda") as response:
                jobj = json.loads(await response.text())
                await ctx.respond(
                    embed=discord.Embed(
                        title="Random Panda", color=discord.Color.dark_grey()
                    ).set_image(url=(jobj.get("link")))
                )
            await session.close()

    @discord.slash_command(name="reverse", description="Reverse the text given")
    @discord.option(name="text", type=str, description="Text to be manipulated")
    @commands.cooldown(1, 3, BucketType.member)
    async def reverse(self, ctx: discord.ApplicationContext, *, text: str):
        await ctx.respond(text[::-1], allowed_mentions=discord.AllowedMentions.none())

    @discord.slash_command(
        name="discriminator",
        description="Get a list of other users with the same dicriminator as you",
    )
    @discord.option(name="discriminator", required=False, type=str)
    @commands.cooldown(1, 7, BucketType.member)
    @discord.guild_only()
    async def discrim(self, ctx: discord.ApplicationContext, *, discriminator: str):
        discriminator = (
            ctx.author.discriminator if not discriminator else discriminator.strip("#")
        )
        embed = discord.Embed(
            title=f"Users with #{discriminator}",
            color=discord.Color.dark_grey(),
        )
        members = [
            str(member)
            for member in ctx.guild.members
            if member.discriminator == discriminator and member != ctx.author
        ]
        embed.description = (
            f"There are no users in this guild with #{discriminator}"
            if len(members) <= 0
            else "\n".join(members)
        )
        file = None
        if len(members) >= 25:
            embed.description = f"There are {len(members):,} users in this guild with that discriminator"
            file = discord.File(
                fp=io.BytesIO("\n".join(members).encode("utf-8")),
                filename=f"{discriminator}.txt",
            )
        await ctx.respond(embed=embed, file=file)

    @discord.slash_command(
        name="leetspeak", description="Translate given text to leetspeak"
    )
    @discord.option(name="text", type=str, description="Text to be manipulated")
    @commands.cooldown(1, 3, BucketType.member)
    async def leet(self, ctx: discord.ApplicationContext, *, text: str):
        leet_table = str.maketrans(
            {
                "a": "4",
                "b": "8",
                "d": "|)",
                "e": "3",
                "g": "9",
                "i": "1",
                "k": "|<",
                "l": "|_",
                "m": "^^",
                "o": "0",
                "p": "|>",
                "q": "<|",
                "s": "5",
                "t": "7",
                "u": "û",
                "v": "\\/",
                "w": "><",
                "x": "><",
                "z": "2",
                " ": " ",
            }
        )
        await ctx.respond(
            text.lower().translate(leet_table),
            allowed_mentions=discord.AllowedMentions.none(),
        )


def setup(bot):
    bot.add_cog(Fun(bot))
