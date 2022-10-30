import contextlib
import difflib
import inspect
import string
import typing

import discord
from discord.ext import commands


class Sent_From(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=180)
        self.add_item(
            item=discord.ui.Button(
                label="Sent from {0}".format(guild.name),
                disabled=True,
                style=discord.ButtonStyle.success,
            )
        )


class JoinDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def color_complete(self, ctx: discord.context.AutocompleteContext) -> list:
        if len(ctx.value) < 1:
            return ["Enter at least 1 character for autocomplete"]
        else:
            choices = [
                color
                for color, thing in inspect.getmembers(discord.Color)
                if callable(thing) and not str(color).startswith("_")
            ]
            return difflib.get_close_matches(ctx.value, choices)

    def convert_message(self, member: discord.Member, message: str):
        variables = {
            "user": member,
            "user_ping": member.mention,
            "user_name": member.name,
            "server_name": member.guild.name,
            "join_position": sum(
                mem.joined_at < member.joined_at
                for mem in member.guild.members
                if mem.joined_at is not None
            ),
        }
        template = string.Template(str(message))
        return str(template.safe_substitute(**variables))

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member):
        record = await self.bot.database.join_dm.find_one(
            {"guild": str(member.guild.id)}
        )
        if record is None:
            return
        with contextlib.suppress(discord.Forbidden, AttributeError):
            embed = discord.Embed(
                title="Hello !",
                color=getattr(discord.Color, record.get("color", "dark_grey"))(),
                description=self.convert_message(
                    member, record.get("message", "Welcome to ${server_name}!")
                ),
            )
            await member.send(embed=embed, view=Sent_From(member.guild))

    joindm = discord.SlashCommandGroup(
        "joindm",
        "Automatically send a custom message to new members.",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    config = joindm.create_subgroup(
        name="config",
        description="Configure the message being sent to users upon joining",
    )

    @joindm.command(
        name="view", description="View the message being sent to users upon joining"
    )
    @discord.guild_only()
    async def view_joindm(self, ctx: discord.ApplicationContext):
        await self.on_member_join(ctx.author)
        await ctx.respond(
            "I've replicated you joining the server. Check your DM's to see how it looks !"
        )

    @joindm.command(
        name="enable", description="Enable sending a message to users upon joining"
    )
    @discord.guild_only()
    async def enable_joindm(self, ctx: discord.ApplicationContext):
        ack = await self.bot.database.join_dm.insert_one(
            {
                "guild": str(ctx.guild.id),
                "color": "dark_grey",
                "message": "Welcome to ${server_name}!",
            }
        )
        if ack.inserted_id:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully enabled Join-DM's, to configure them use /joindm config.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Unable to enable Join-DM's.")

    @joindm.command(
        name="disable", description="Disable sending a message to users upon joining"
    )
    @discord.guild_only()
    async def disable_joindm(self, ctx: discord.ApplicationContext):
        ack = await self.bot.database.join_dm.delete_one({"guild": str(ctx.guild.id)})
        if ack.deleted_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully disabled Join-DM's.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Unable to disable Join-DM's.")

    @config.command(name="color", description="Set embed color")
    @discord.option(
        name="new_color",
        type=str,
        description="Embed color",
        autocomplete=color_complete,
    )
    @discord.guild_only()
    async def set_color(self, ctx: discord.ApplicationContext, new_color: str):
        if new_color not in [
                color
                for color, thing in inspect.getmembers(discord.Color)
                if callable(thing) and not str(color).startswith("_")
            ]:
            return await self.bot.respond_error("Invalid color, please choose one from ")
        ack = await self.bot.database.join_dm.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"color": new_color}}
        )
        if ack.modified_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="Successfully changed embed color.",
                    color=getattr(discord.Color, new_color)(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Embed color was not modified")

    @config.command(name="message", description="Set embed message")
    @discord.option(
        name="new_message",
        type=str,
        description="Embed message",
    )
    @discord.guild_only()
    async def set_message(self, ctx: discord.ApplicationContext, new_message: str):
        ack = await self.bot.database.join_dm.update_one(
            {"guild": str(ctx.guild.id)}, {"$set": {"message": new_message}}
        )
        if ack.modified_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"Successfully changed embed message to ```\n{new_message}\n```",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Embed color was not modified")


def setup(bot):
    bot.add_cog(JoinDM(bot))
