import contextlib
import io
import json
import random
import typing

import aiohttp
import discord
import humanize
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

bool_to_emoji = lambda b: "✅" if b else "❌"
human_status = lambda status: {
    "dnd": "Do Not Disturb.",
    "online": "Online.",
    "idle": "Idle.",
    "offline": "Offline.",
}.get(status, "Error.")


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="avatar", description="View user's avatar")
    @discord.option(
        name="member", type=discord.Member, required=False, description="Member to view"
    )
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def avatar(
        self, ctx: discord.ApplicationContext, member: typing.Optional[discord.Member]
    ):
        member = member if member != None else ctx.author
        try:
            _128 = (member.display_avatar.with_size(128)).url
            _256 = (member.display_avatar.with_size(256)).url
            _512 = (member.display_avatar.with_size(512).with_format("png")).url
            _1024 = (member.display_avatar.with_size(1024)).url
            _2048 = (member.display_avatar.with_size(2048)).url
            embed = discord.Embed(
                color=discord.Color.dark_grey(),
                description="**[ [128]({}) ] - [ [256]({}) ] - [ 512 ] - [ [1024]({}) ] - [ [2048]({}) ]**".format(
                    _128, _256, _1024, _2048
                ),
            )
            embed.set_image(url="attachment://512.png")
            embed.set_footer(text="{}'s Avatar (512 x 512)".format(member))
            async with aiohttp.ClientSession() as session:
                async with session.get(_512) as resp:
                    await ctx.respond(
                        embed=embed,
                        file=discord.File(
                            fp=io.BytesIO(await resp.read()), filename="512.png"
                        ),
                    )
                await session.close()
        except AttributeError:
            return await self.bot.respond_error(ctx, "Member does not have a avatar.")

    @discord.slash_command(name="servericon", description="View guild's icon")
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def guildicon(self, ctx: discord.ApplicationContext):
        try:
            _128 = (ctx.guild.icon.with_size(128)).url
            _256 = (ctx.guild.icon.with_size(256)).url
            _512 = (ctx.guild.icon.with_size(512)).url
            _1024 = (ctx.guild.icon.with_size(1024)).url
            _2048 = (ctx.guild.icon.with_size(2048)).url
            embed = discord.Embed(
                color=discord.Color.dark_grey(),
                description="**[ [128]({}) ] - [ [256]({}) ] - [ 512 ] - [ [1024]({}) ] - [ [2048]({}) ]**".format(
                    _128, _256, _1024, _2048
                ),
            )
            embed.set_image(url=_512)
        except AttributeError:
            return await self.bot.respond_error(ctx, "Guild does not have an icon.")
        await ctx.respond(embed=embed)

    @discord.slash_command(aliases=["b"], description="View user's profile banner")
    @discord.option(
        name="member", type=discord.Member, required=False, description="Member to view"
    )
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def banner(
        self, ctx: discord.ApplicationContext, member: typing.Optional[discord.Member]
    ):
        member = await self.bot.fetch_user(
            (member if member != None else ctx.author).id
        )
        try:
            _512 = (member.banner.with_size(512)).url
            _1024 = (member.banner.with_size(1024)).url
            _2048 = (member.banner.with_size(2048)).url
            embed = discord.Embed(
                color=discord.Color.dark_grey(),
                description="**[ 512 ] - [ [1024]({}) ] - [ [2048]({}) ]**".format(
                    _1024, _2048
                ),
            )
            embed.set_image(url=_512)
        except AttributeError:
            return await self.bot.respond_error(
                ctx, "Member does not have a profile banner."
            )
        embed.set_footer(text="{}'s Banner".format(member))
        await ctx.respond(embed=embed)

    @discord.slash_command(description="View ban count for current server")
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def bancount(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            embed=discord.Embed(
                color=discord.Color.dark_grey(),
                title="Ban Count",
                description="**{0}** has `{1}` bans".format(
                    ctx.guild.name, len(await ctx.guild.bans().flatten())
                ),
            )
        )

    @discord.slash_command(
        name="membercount", description="Displays amount of members in guild"
    )
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def membercount(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title=ctx.guild.name,
            description=f"`{str(ctx.guild.member_count)}` member(s)",
            color=discord.Color.dark_grey(),
        )
        with contextlib.suppress(AttributeError):
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.respond(embed=embed)

    @discord.slash_command(name="serverbanner", description="View guild's banner")
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def guildbanner(self, ctx: discord.ApplicationContext):
        try:
            _512 = (ctx.guild.banner.with_size(512)).url
            _1024 = (ctx.guild.banner.with_size(1024)).url
            _2048 = (ctx.guild.banner.with_size(2048)).url
            embed = discord.Embed(
                color=discord.Color.dark_grey(),
                description="**[ 512 ] - [ [1024]({}) ] - [ [2048]({}) ]**".format(
                    _1024, _2048
                ),
            )
            embed.set_image(
                url=(
                    _512 if not ctx.guild.banner.is_animated() else ctx.guild.banner.url
                )
            )
        except AttributeError:
            return await self.bot.respond_error(ctx, "Guild does not have a banner.")
        await ctx.respond(embed=embed)

    @discord.slash_command(name="whois", description="Info about a user")
    @discord.option(
        name="member", type=discord.Member, required=False, description="Member to view"
    )
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def whois(
        self, ctx: discord.ApplicationContext, member: typing.Optional[discord.Member]
    ):
        member: discord.Member = member if member != None else ctx.author
        roleNameList = list(
            role.mention for role in member.roles if role != ctx.guild.default_role
        )
        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.set_author(
            name="{} ({})".format(member, member.id), icon_url=member.display_avatar.url
        )
        embed.add_field(
            name="Basic Info",
            value="Joined Server At - **{} ({})**\nRegistered on Discord At - **{} ({})**".format(
                discord.utils.format_dt(member.joined_at, "D"),
                discord.utils.format_dt(member.joined_at, "R"),
                discord.utils.format_dt(member.created_at, "D"),
                discord.utils.format_dt(member.created_at, "R"),
            ),
        )
        embed.add_field(
            name="Status Info (Buggy)",
            value="Desktop Status - **{}**\nMobile Status - **{}**\nWeb Application Status - **{}**".format(
                human_status(str(member.desktop_status)),
                human_status(str(member.mobile_status)),
                human_status(str(member.web_status)),
            ),
            inline=False,
        )
        embed.add_field(
            name="Role Info",
            value="Top Role - {}\nRole(s) - {}".format(
                member.top_role.mention
                if member.top_role != ctx.guild.default_role
                else "None",
                ", ".join(roleNameList).removesuffix(", ")
                if roleNameList != []
                else "None",
            ),
            inline=False,
        )
        embed.add_field(
            name="Flags",
            value="{} - Discord Staff\n{} - Discord Partner\n{} - Verified Bot Developer".format(
                bool_to_emoji(member.public_flags.staff),
                bool_to_emoji(member.public_flags.partner),
                bool_to_emoji(member.public_flags.verified_bot_developer),
            ),
        )
        embed.add_field(
            name="Key Permissions",
            value="- Administrator {0}\n- Manage Server {1}\n- Manage Channels {2}\n- Manage Roles {3}\n- Manage Messages {4}\n- Kick Members {5}\n- Ban Members {6}".format(
                bool_to_emoji(member.guild_permissions.administrator),
                bool_to_emoji(member.guild_permissions.manage_channels),
                bool_to_emoji(member.guild_permissions.manage_roles),
                bool_to_emoji(member.guild_permissions.manage_messages),
                bool_to_emoji(member.guild_permissions.administrator),
                bool_to_emoji(member.guild_permissions.kick_members),
                bool_to_emoji(member.guild_permissions.ban_members),
            ),
            inline=False,
        )
        embed.set_footer(
            icon_url=ctx.author.display_avatar.url,
            text="Requested By: {}".format(ctx.author.name),
        )
        await ctx.respond(embed=embed)

    @discord.slash_command(name="serverinfo", description="Info about this server")
    @commands.cooldown(1, 5, type=BucketType.member)
    @discord.guild_only()
    async def serverinfo(self, ctx: discord.ApplicationContext):
        findbots = sum(1 for member in ctx.guild.members if member.bot)
        vanity = "VANITY_URL" in str(ctx.guild.features)
        splash = "INVITE_SPLASH" in str(ctx.guild.features)
        animicon = "ANIMATED_ICON" in str(ctx.guild.features)
        discoverable = "DISCOVERY" in str(ctx.guild.features)
        banner = "BANNER" in str(ctx.guild.features)
        vanityFeature = (
            "{} - Vanity URL".format(bool_to_emoji(vanity))
            if not vanity
            else "{} - Vanity URL (**{}**)".format(
                bool_to_emoji(vanity), str(await ctx.guild.vanity_invite())[15:]
            )
        )
        embed = discord.Embed(
            title="**{}**".format(ctx.guild.name), colour=discord.Color.dark_grey()
        )
        with contextlib.suppress(AttributeError):
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(
            name="Members",
            value="Bots: **{}**\nHumans: **{}**\nOnline Members: **{}/{}**".format(
                str(findbots),
                ctx.guild.member_count - findbots,
                sum(
                    member.status != discord.Status.offline and not member.bot
                    for member in ctx.guild.members
                ),
                str(ctx.guild.member_count),
            ),
        )
        embed.add_field(
            name="Channels",
            value="\U0001f4ac Text Channels: **{}**\n\U0001f50a Voice Channels: **{}**".format(
                len(ctx.guild.text_channels), len(ctx.guild.voice_channels)
            ),
        )
        embed.add_field(
            name="Important Info",
            value="Owner: {}\nVerification Level: **{}**\nGuild ID: **{}**".format(
                ctx.guild.owner.mention,
                str(ctx.guild.verification_level).title(),
                ctx.guild.id,
            ),
            inline=False,
        )
        embed.add_field(
            name="Other Info",
            value="AFK Channel: **{}**\n AFK Timeout: **{} minute(s)**\nCustom Emojis: **{}**\nRole Count: **{}**\nFilesize Limit - **{}**".format(
                ctx.guild.afk_channel,
                str(ctx.guild.afk_timeout / 60),
                len(ctx.guild.emojis),
                len(ctx.guild.roles),
                humanize.naturalsize(ctx.guild.filesize_limit),
            ),
            inline=False,
        )
        embed.add_field(
            name="Server Features",
            value="{} - Banner\n{}\n{} - Splash Invite\n{} - Animated Icon\n{} - Server Discoverable".format(
                bool_to_emoji(banner),
                vanityFeature,
                bool_to_emoji(splash),
                bool_to_emoji(animicon),
                bool_to_emoji(discoverable),
            ),
        )
        embed.add_field(
            name="Boost Info",
            value="Number of Boosts - **{}**\nBooster Role - **{}**\nBoost Level/Tier - **{}**".format(
                str(ctx.guild.premium_subscription_count),
                ctx.guild.premium_subscriber_role.mention
                if ctx.guild.premium_subscriber_role != None
                else ctx.guild.premium_subscriber_role,
                ctx.guild.premium_tier,
            ),
        )
        with contextlib.suppress(AttributeError):
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
