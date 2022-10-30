# -*- coding: utf-8 -*-

import asyncio
import datetime
import enum
import re
from collections import defaultdict
from datetime import timedelta
import unicodedata

import discord
from discord.colour import Color
from discord.ext import commands, tasks

normalize = (
    lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf8")
)

bool_emoji = lambda b: "\U00002705" if b else "\U0000274C"


class AntiRaidViolation(enum.Enum):
    USERNAME = "Your username is consistent with raids"
    USERNAME_LENGTH = "Your username is too long"
    AVATAR = "You have no avatar"
    AGE = "Your account was made too recently"


class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.username_regex = re.compile(
            r"tokens|gg/|gg /|raid", flags=re.IGNORECASE | re.MULTILINE
        )
        self.member_map = defaultdict(set)
        self.told_owner = defaultdict(bool)

    async def escort(
        self, member: discord.Member, violation: AntiRaidViolation
    ) -> None:
        embed = discord.Embed(
            color=Color.dark_grey(),
            title="Ross Anti-Raid",
            description="You have been banned from `{0}`".format(member.guild.name),
        )
        embed.add_field(name="Why?", value=violation.value)
        embed.add_field(
            name="When?", value=discord.utils.format_dt(datetime.datetime.utcnow(), "R")
        )
        await member.send(embed=embed)
        await member.ban(delete_message_seconds=86400, reason="Ross Anti-Raid")

    @tasks.loop(seconds=30)
    async def clear_map(self):
        print("cleared")
        self.member_map.clear()

    async def cleanup_map(self, map: set):
        for member in map:
            await member.ban(reason="Ross Anti-Raid", delete_message_days=7)

    def check_username(self, member: discord.Member) -> None:
        if bool(self.username_regex.findall(normalize(member.name))):
            asyncio.ensure_future(
                self.escort(member, AntiRaidViolation.USERNAME), loop=self.bot.loop
            )

    def check_avatar(self, member: discord.Member) -> None:
        if bool(member.avatar == None):
            asyncio.ensure_future(
                self.escort(member, AntiRaidViolation.AVATAR), loop=self.bot.loop
            )

    def check_age(self, member: discord.Member, days: int) -> None:
        if bool(
            (
                datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                - member.created_at.replace(tzinfo=datetime.timezone.utc)
            )
            < timedelta(days)
        ):
            asyncio.ensure_future(
                self.escort(member, AntiRaidViolation.AGE), loop=self.bot.loop
            )

    @commands.Cog.listener("on_member_join")
    async def raid_dispatch(self, member: discord.Member):
        config = await self.bot.database.anti_raid.find_one(
            {"guild": str(member.guild.id)}
        )
        if config is None:
            return
        if config:
            if config.get("username"):
                self.check_username(member)
            if config.get("age").get("enabled"):
                self.check_age(member, config.get("age").get("minimum"))
            if config.get("avatar"):
                self.check_avatar(member)
            self.member_map[member.guild.id].add(member)
            if len(self.member_map[member.guild.id]) >= 5:
                asyncio.ensure_future(
                    self.cleanup_map(self.member_map[member.guild.id].copy())
                )
                self.member_map[member.guild.id].clear()

    antiraid = discord.SlashCommandGroup(
        "antiraid",
        "Prevent raids automatically",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    config = antiraid.create_subgroup(
        name="config",
        description="Configure the Anti-Raid system",
    )

    @antiraid.command(name="view", description="View the current configuration")
    @discord.guild_only()
    async def view_antiraid(self, ctx: discord.ApplicationContext):
        ack = await self.bot.database.anti_raid.find_one({"guild": str(ctx.guild.id)})
        if ack is None:
            return await self.bot.respond_error(
                ctx, "Anti-Raid is not enabled, to enable it use /antiraid enable"
            )
        embed = discord.Embed(
            title="Ross Anti-Raid",
            color=discord.Color.dark_grey(),
            description=f"""
            \r**Check Username**: {bool_emoji(ack.get("username"))}
            \r**Avatar Required**: {bool_emoji(ack.get("avatar"))}
            \r**Account Age**: {bool_emoji(ack.get("age").get("enabled"))}\n - **Minimum**: `{ack.get("age").get("minimum")} days`
            """,
        )
        await ctx.respond(embed=embed)

    @antiraid.command(name="enable", description="Enable the Anti-Raid system")
    @discord.guild_only()
    async def enable_antiraid(self, ctx: discord.ApplicationContext):
        try:
            ack = await self.bot.database.anti_raid.insert_one(
                {
                    "guild": str(ctx.guild.id),
                    "username": True,
                    "age": {"enabled": True, "minimum": 5},
                    "avatar": False,
                }
            )
        except:
            await self.bot.respond_error(ctx, "Unable to enable Anti-Raid.")
        if ack.inserted_id:
            await self.bot.respond_success(ctx, "Successfully enabled Anti-Raid, to configure it use /antiraid config.")
        else:
            await self.bot.respond_error(ctx, "Unable to enable Anti-Raid.")

    @antiraid.command(name="disable", description="Disable the Anti-Raid system")
    @discord.guild_only()
    async def disable_antiraid(self, ctx: discord.ApplicationContext):
        ack = await self.bot.database.anti_raid.delete_one({"guild": str(ctx.guild.id)})
        if ack.deleted_count > 0:
            await self.bot.respond_success(ctx, "Successfully disabled Anti-Raid.")
        else:
            await self.bot.respond_error(ctx, "Unable to disable Anti-Raid.")

    @config.command(
        name="username", description="Toggle searching for malicious usernames."
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
    async def set_username_check(self, ctx: discord.ApplicationContext, status: int):
        ack = await self.bot.database.anti_raid.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"username": bool(status)}}
        )
        if ack.modified_count > 0:
            await self.bot.respond_success(ctx, "Successfully updated malicious username check.")
        else:
            await self.bot.respond_error(
                ctx, "Malicious username check was not modified."
            )

    @config.command(name="avatar", description="Toggle requiring an avatar.")
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
        ack = await self.bot.database.anti_raid.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"avatar": bool(status)}}
        )
        if ack.modified_count > 0:
            await self.bot.respond_success(ctx, "Successfully updated avatar requirement.")
        else:
            await self.bot.respond_error(ctx, "Avatar requirement was not modified.")

    @config.command(name="age", description="Set minimum user account age")
    @discord.option(
        name="days",
        description="How many days old should a user's account be?",
        choices=[
            discord.OptionChoice(name="3 days", value=3),
            discord.OptionChoice(name="1 week", value=7),
            discord.OptionChoice(name="1 month", value=30),
            discord.OptionChoice(name="Disable Feature", value=-1),
        ],
    )
    @discord.guild_only()
    async def set_age_requirement(self, ctx: discord.ApplicationContext, days: int):
        if days <= 0:
            ack = await self.bot.database.anti_raid.update_one(
                {"guild": str(ctx.guild.id)}, {"$set": {"age.enabled": False}}
            )
        ack = await self.bot.database.anti_raid.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"age.minimum": int(days)}}
        )
        if ack.modified_count > 0:
            await self.bot.respond_success(ctx, "Successfully updated age requirement.")
        else:
            await self.bot.respond_error(ctx, "Age requirement was not modified.")


def setup(bot):
    bot.add_cog(AntiRaid(bot))
