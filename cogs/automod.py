# -*- coding: utf-8 -*-

import asyncio
import collections
import contextlib
import datetime
import re
import unicodedata

import aiohttp
import aiohttp.client_exceptions
import discord
from discord.colour import Color
from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import CooldownMapping

normalize = (
    lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf8")
)

bool_emoji = lambda b: "\U00002705" if b else "\U0000274C"


class Automod(commands.Cog, description="Automatic Moderation"):
    def __init__(self, bot):
        self.bot = bot
        self._URL_REGEX = re.compile(
            r"(?:\<?(?:.*)*\:\/\/(?:.*)*\/?\>?)", flags=re.IGNORECASE
        )
        self.invite_regex = re.compile(
            r"top.gg/|discord.gg/|discord.com/invite/|.gg/|discord.io/|dsc.gg/|join /(?:.*)",
            flags=re.MULTILINE | re.IGNORECASE,
        )
        self.spam_count = collections.defaultdict(int)
        self.map: CooldownMapping = commands.CooldownMapping.from_cooldown(
            5, 3, commands.BucketType.member
        )

    async def mute_user(self, message: discord.Message):
        del self.spam_count[message.author.id]
        with contextlib.suppress(discord.Forbidden):
            await message.author.timeout(until=None, reason="Auto-Mod")
        await message.channel.purge(
            limit=10, bulk=True, check=lambda m: message.author.id == m.author.id
        )
        with contextlib.suppress(Exception):
            await message.author.send(
                embed=discord.Embed(
                    title="You have been muted",
                    color=discord.Color.dark_grey(),
                    description="You have been muted in `{0}` for `{1}` as of {2}".format(
                        message.guild.name,
                        "Repeated Spamming",
                        discord.utils.format_dt(datetime.datetime.now(), "f"),
                    ),
                )
            )
        await message.channel.send(
            embed=discord.Embed(
                title="Ross Auto-Mod",
                color=Color.dark_grey(),
                description="`%s` has been muted for repeated spamming."
                % (message.author),
            )
        )

    @tasks.loop(minutes=2)
    async def clear_counter(self):
        self.spam_count.clear()

    @commands.Cog.listener("on_message")
    async def automod_dispatch(self, message: discord.Message):
        with contextlib.suppress(Exception):
            if message.author.bot:
                return
            if not message.guild:
                return
            record = await self.bot.database.auto_mod.find_one(
                {"guild": str(message.guild.id)}
            )
            config = record.get("config")
            if bool(config.get("profanity")):
                asyncio.ensure_future(
                    self.profanity_filter(message), loop=self.bot.loop
                )
            # if bool(config.get("spam")):
            #     asyncio.ensure_future(self.spam_filter(message), loop=self.bot.loop)
            if bool(config.get("invite")):
                asyncio.ensure_future(self.invite_filter(message), loop=self.bot.loop)
            if bool(config.get("link")):
                asyncio.ensure_future(self.link_filter(message), loop=self.bot.loop)
            if bool(self._URL_REGEX.findall(message.clean_content)):
                asyncio.ensure_future(self.rickroll_filter(message), loop=self.bot.loop)
            if bool(message.mentions):
                if bool(config.get("mentions").get("enabled")):
                    asyncio.ensure_future(
                        self.mention_filter(
                            message, int(config.get("mentions").get("amount"))
                        ),
                        loop=self.bot.loop,
                    )

    @commands.Cog.listener("on_message_edit")
    async def automod_edit_dispatch(self, _, after: discord.Message):
        await self.automod_dispatch(after)

    # async def spam_filter(self, message: discord.Message):
    #     # if message.author.guild_permissions.administrator:
    #     #     return
    #     bucket = self.map.get_bucket(message)
    #     now = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
    #     bucket_full = bucket.update_rate_limit(now)
    #     if bucket_full:
    #         self.spam_count[message.author.id] += 1
    #         await message.channel.send(
    #             embed=discord.Embed(
    #                 color=discord.Color.dark_grey(),
    #                 description="{0} Woah Woah ! Slow down bud, no spamming. This is your {1}/2 warning.".format(
    #                     message.author.mention, self.spam_count[message.author.id]
    #                 ),
    #             ),
    #             delete_after=5,
    #         )
    #         await message.channel.purge(
    #             limit=15,
    #             bulk=True,
    #             check=lambda m: message.author.id == m.author.id,
    #         )
    #         bucket.reset()
    #     with contextlib.suppress(KeyError):
    #         if self.spam_count[message.author.id] >= 3:
    #             asyncio.ensure_future(self.mute_user(message), loop=self.bot.loop)

    async def invite_filter(self, message: discord.Message):
        if message.author.guild_permissions.administrator:
            return
        if bool(self.invite_regex.findall(normalize(str(message.clean_content)))):
            with contextlib.suppress(Exception):
                await message.delete()

    async def link_filter(self, message: discord.Message):
        if message.author.guild_permissions.administrator:
            return
        if bool(self._URL_REGEX.findall(normalize(str(message.clean_content)))):
            with contextlib.suppress(Exception):
                await message.delete()

    async def mention_filter(self, message: discord.Message, max_mentions: int):
        if len(message.mentions) >= max_mentions:
            if not message.author.guild_permissions.administrator:
                with contextlib.suppress(Exception):
                    await message.delete()
                    for target in message.mentions:
                        await target.send(f"You were ghost pinged in `{message.guild.name}` by {message.author}")

    async def rickroll_filter(self, message: discord.Message):
        with contextlib.suppress(IndexError, aiohttp.client_exceptions.InvalidURL):
            rick_emojis = ["\U0001F1F7", "\U0001F1EE", "\U0001F1E8", "\U0001F1F0"]
            phrases = [
                "rickroll",
                "rick roll",
                "rick astley",
                "never gonna give you up",
            ]
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._URL_REGEX.findall(string=message.content)[0],
                    allow_redirects=True,
                ) as resp:
                    source = str(await resp.content.read()).casefold()
                    rickRoll = bool(
                        (
                            re.findall(
                                "|".join(phrases), source, re.MULTILINE | re.IGNORECASE
                            )
                        )
                    )
                    if rickRoll:
                        with contextlib.suppress(Exception):
                            [await message.add_reaction(emoji) for emoji in rick_emojis]
                await session.close()

    async def profanity_filter(self, message: discord.Message):
        if message.author.guild_permissions.administrator:
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://free-public-api.herokuapp.com/validate_bad_words/?input={0}&lang=en".format(
                    message.clean_content
                )
            ) as response:
                if not bool(await response.text() == "false"):
                    await message.delete()
            await session.close()

    automod = discord.SlashCommandGroup(
        "automod",
        "Automatically moderate your server",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    config = automod.create_subgroup(
        name="config",
        description="Configure the Auo-Moderation system",
    )

    @automod.command(name="view", description="View the current configuration")
    @discord.guild_only()
    async def view_automod(self, ctx: discord.ApplicationContext):
        ack = await self.bot.database.auto_mod.find_one({"guild": str(ctx.guild.id)})
        if ack is None:
            return await self.bot.respond_error(
                ctx, "Auto-Moderation is not enabled, to enable it use /automod enable"
            )
        embed = discord.Embed(
            title="Ross Auto-Moderation",
            color=discord.Color.dark_grey(),
            description=f"""
            \r**Profanity Filter**: {bool_emoji(ack.get("config").get("profanity"))}
            \r**Invite Filter**: {bool_emoji(ack.get("config").get("invite"))}
            \r**Link Filter**: {bool_emoji(ack.get("config").get("invite"))}
            \r**Rick-Roll Warning**: {bool_emoji(ack.get("config").get("rickroll"))}
            \r**Mention Filter**: {bool_emoji(ack.get("config").get("mentions").get("enabled"))}\n - **Maximum**: `{ack.get("config").get("mentions").get("amount")} mentions`
            """,
        )
        await ctx.respond(embed=embed)

    @automod.command(name="enable", description="Enable the Auto-Moderation system")
    @discord.guild_only()
    async def enable_automod(self, ctx: discord.ApplicationContext):
        try:
            ack = await self.bot.database.auto_mod.insert_one(
                {
                    "guild": str(ctx.guild.id),
                    "config": {
                        "profanity": False,
                        "invite": True,
                        "link": True,
                        "rickroll": True,
                        "mentions": {"enabled": True, "amount": 5},
                    },
                }
            )
        except:
            await self.bot.respond_error(ctx, "Unable to enable Auto-Moderation.")
        if ack.inserted_id:
            await self.bot.respond_success(ctx, "Successfully enabled Auto-Moderation, to configure it use /automod config.")
        else:
            await self.bot.respond_error(ctx, "Unable to enable Auto-Moderation.")

    @automod.command(name="disable", description="Disable the Auto-Moderation system")
    @discord.guild_only()
    async def disable_automod(self, ctx: discord.ApplicationContext):
        ack = await self.bot.database.auto_mod.delete_one({"guild": str(ctx.guild.id)})
        if ack.deleted_count > 0:
            await self.bot.respond_error(ctx, "Successfully disabled Auto-Moderation.")
        else:
            await self.bot.respond_error(ctx, "Unable to disable Auto-Moderation.")

    @config.command(
        name="profanity", description="Toggle filtering profanity."
    )
    @discord.option(
        name="status",
        description="Should this feature be enabled?",
        choices=[
            discord.OptionChoice(name="Enabled", value=1),
            discord.OptionChoice(name="Disabled", value=0),
        ],
    )
    @discord.guild_only()
    async def set_profanity_filter(self, ctx: discord.ApplicationContext, status: int):
        ack = await self.bot.database.auto_mod.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"config.profanity": bool(status)}}
        )
        if ack.modified_count > 0:
            await self.bot.respond_success(ctx, "Successfully updated profanity filter.")
        else:
            await self.bot.respond_error(
                ctx, "Profanity filter was not modified."
            )

    @config.command(name="invite", description="Toggle filtering invites.")
    @discord.option(
        name="status",
        description="Should this feature be enabled?",
        choices=[
            discord.OptionChoice(name="Enabled", value=1),
            discord.OptionChoice(name="Disabled", value=0),
        ],
    )
    @discord.guild_only()
    async def set_avatar_required(self, ctx: discord.ApplicationContext, status: int):
        ack = await self.bot.database.auto_mod.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"config.invite": bool(status)}}
        )
        if ack.modified_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully updated invite filter.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Invite filter was not modified.")

    @config.command(name="link", description="Toggle filtering links.")
    @discord.option(
        name="status",
        description="Should this feature be enabled?",
        choices=[
            discord.OptionChoice(name="Enabled", value=1),
            discord.OptionChoice(name="Disabled", value=0),
        ],
    )
    @discord.guild_only()
    async def set_avatar_required(self, ctx: discord.ApplicationContext, status: int):
        ack = await self.bot.database.auto_mod.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"config.link": bool(status)}}
        )
        if ack.modified_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully updated link filter.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Link filter was not modified.")

    @config.command(name="rickroll", description="Toggle Rick-Roll warnings.")
    @discord.option(
        name="status",
        description="Should this feature be enabled?",
        choices=[
            discord.OptionChoice(name="Enabled", value=1),
            discord.OptionChoice(name="Disabled", value=0),
        ],
    )
    @discord.guild_only()
    async def set_avatar_required(self, ctx: discord.ApplicationContext, status: int):
        ack = await self.bot.database.auto_mod.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"config.rickroll": bool(status)}}
        )
        if ack.modified_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully updated rick-roll warnings.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Rick-Roll warnings were not modified.")

    @config.command(name="mentions", description="Set maximum amount of mentions in a message")
    @discord.option(
        name="amount",
        description="How many should the maximum amount of mentions be?",
        choices=[
            discord.OptionChoice(name="3", value=3),
            discord.OptionChoice(name="7", value=7),
            discord.OptionChoice(name="10", value=10),
            discord.OptionChoice(name="Disable Feature", value=-1),
        ],
    )
    @discord.guild_only()
    async def set_age_requirement(self, ctx: discord.ApplicationContext, amount: int):
        if amount <= 0:
            ack = await self.bot.database.auto_mod.update_one(
                {"guild": str(ctx.guild.id)}, {"$set": {"config.mentions.enabled": False}}
            )
        ack = await self.bot.database.auto_mod.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"config.mentions.amount": int(amount)}}
        )
        if ack.modified_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully updated maximum amount of mentions.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Age requirement was not modified.")


def setup(bot):
    bot.add_cog(Automod(bot))
