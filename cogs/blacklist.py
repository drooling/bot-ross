import contextlib
import difflib
import unicodedata

import discord
from discord.errors import NotFound
from discord.ext import commands

normalize = (
    lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf8")
)


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def blacklist_complete(self, ctx: discord.AutocompleteContext):
        choices = await (
            self.bot.database.blacklist.find({"guild": str(ctx.interaction.guild.id)})
        ).to_list(length=None)
        if len(choices) < 25:
            return [r.get("term") for r in choices]
        else:
            if len(ctx.value) < 1:
                return ["Enter at least 1 character for autocompletion"]
            return difflib.get_close_matches(
                ctx.value, [r.get("term") for r in choices], cutoff=0.2
            )

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if isinstance(message.author, discord.User):
            return
        if message.author.id is self.bot.user.id:
            return
        if message.author.guild_permissions.administrator:
            return
        async for record in self.bot.database.blacklist.find(
            {"guild": str(message.guild.id)}
        ):
            if normalize(message.clean_content.casefold()).__contains__(
                str(record.get("term")).casefold()
            ):
                with contextlib.suppress(NotFound):
                    return await message.delete()

    blacklist = discord.SlashCommandGroup(
        "blacklist",
        "Automatically delete messages containing blacklisted terms.",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    @blacklist.command(name="add", description="Add a new term to the blacklist")
    @discord.option(
        name="term", type=str, description="The term to add to the blacklist"
    )
    @discord.guild_only()
    async def add_blacklist(self, ctx: discord.ApplicationContext, term: str):
        ack = await self.bot.database.blacklist.insert_one(
            {"guild": str(ctx.guild.id), "term": term}
        )
        if ack.inserted_id:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"Successfully added `{term}` to the blacklist.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Blacklist was not modified.")

    @blacklist.command(name="remove", description="Remove a term from the blacklist")
    @discord.option(
        name="term",
        type=str,
        description="The term to remove from blacklist",
        autocomplete=blacklist_complete,
    )
    @discord.guild_only()
    async def remove_blacklist(self, ctx: discord.ApplicationContext, term: str):
        ack = await self.bot.database.blacklist.delete_one(
            {"guild": str(ctx.guild.id), "term": term}
        )
        if ack.deleted_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"Successfully removed `{term}` from the blacklist.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Blacklist was not modified.")


def setup(bot):
    bot.add_cog(Blacklist(bot))
