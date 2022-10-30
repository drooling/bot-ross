import contextlib
import difflib
from discord.ext import commands
import discord


class StickyNick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_member_update")
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        record = await self.bot.database.sticky_nick.find_one(
            {"guild": str(after.guild.id), "member": str(after.id)}
        )
        if record:
            sticky_nick = record.get("new_nick")
            if after.nick == str(sticky_nick):
                return
            else:
                with contextlib.suppress(discord.Forbidden):
                    await after.edit(
                        nick=str(sticky_nick), reason="Ross Sticky Nicknames"
                    )

    stickynick = discord.SlashCommandGroup(
        name="stickynick",
        description="Automatically change a member's nickname",
        checks=[commands.has_guild_permissions(manage_nicknames=True).predicate],
    )

    @stickynick.command(name="add", description="Add a new sticky nickname")
    @discord.option(name="member", type=discord.Member, description="The target member")
    @discord.option(
        name="new_nick", type=str, description="The new nickname to change to"
    )
    @discord.guild_only()
    async def add_stickynick(
        self, ctx: discord.ApplicationContext, member: discord.Member, new_nick: str
    ):
        try:
            ack = await self.bot.database.sticky_nick.insert_one(
                {"guild": str(ctx.guild.id), "member": str(member.id), "new_nick": new_nick}
            )
        except:
            return await self.bot.respond_error(ctx, "Sticky-Nicknames were not modified.")
        await member.edit(nick=new_nick)
        if ack.inserted_id:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"Successfully added `{new_nick}` as a sticky-nickname for {member.mention}",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            return await self.bot.respond_error(ctx, "Sticky-Nicknames were not modified.")

    @stickynick.command(
        name="remove", description="Remove a user's sticky-nick"
    )
    @discord.option(
        name="member",
        type=discord.Member,
        description="The Status-Role to remove.",
    )
    @discord.guild_only()
    async def remove_statusroles(self, ctx: discord.ApplicationContext, member: discord.Member):
        ack = await self.bot.database.sticky_nick.delete_one(
            {"guild": str(ctx.guild.id), "member": str(member.id)}
        )
        if ack.deleted_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"{member.mention}'s sticky-nick has been removed.",
                    color=discord.Color.dark_grey(),
                ),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await self.bot.respond_error(ctx, "Sticky-Nicknames were not modified.")


def setup(bot):
    bot.add_cog(StickyNick(bot))
