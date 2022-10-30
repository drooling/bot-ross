import contextlib
import datetime
import difflib
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType


class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def responder_complete(self, ctx: discord.AutocompleteContext):
        choices = await (
            self.bot.database.auto_responder.find(
                {"guild": str(ctx.interaction.guild.id)}
            )
        ).to_list(length=None)
        if len(choices) < 25:
            return [r.get("keyword") for r in choices]
        else:
            if len(ctx.value) < 1:
                return ["Enter at least 1 character for autocompletion"]
            return difflib.get_close_matches(
                ctx.value, [r.get("keyword") for r in choices], cutoff=0.2
            )

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author == self.bot.user:
            return
        async for record in self.bot.database.auto_responder.find(
            {"guild": str(message.guild.id)}
        ):
            if message.clean_content.casefold().__contains__(
                str(record.get("keyword")).casefold()
            ):
                return await message.reply(
                    record.get("response"),
                    allowed_mentions=discord.AllowedMentions.none(),
                )

    autoresponder = discord.SlashCommandGroup(
        "autoresponder",
        "Automatically respond with specified response when a keyword is found in a message",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    @autoresponder.command(
        name="add", description="Add a new keyword to the Auto-Responder"
    )
    @discord.option(
        name="keyword", type=str, description="The keyword to add to the Auto-Responder"
    )
    @discord.option(
        name="response",
        type=str,
        description="The response to send when the keyword is found",
    )
    @discord.guild_only()
    async def add_autoresponder(
        self, ctx: discord.ApplicationContext, keyword: str, response: str
    ):
        ack = await self.bot.database.auto_responder.insert_one(
            {"guild": str(ctx.guild.id), "keyword": keyword, "response": response}
        )
        if ack.inserted_id:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"Successfully added `{keyword}` to the Auto-Responder.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Auto-Responder was not modified.")

    @autoresponder.command(
        name="remove", description="Remove a keyword from the Auto-Responder"
    )
    @discord.option(
        name="keyword",
        type=str,
        description="The keyword to remove from Auto-Responder",
        autocomplete=responder_complete,
    )
    @discord.guild_only()
    async def remove_autoresponder(self, ctx: discord.ApplicationContext, keyword: str):
        ack = await self.bot.database.auto_responder.delete_one(
            {"guild": str(ctx.guild.id), "keyword": keyword}
        )
        if ack.deleted_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"Successfully removed `{keyword}` from the Auto-Responder.",
                    color=discord.Color.dark_grey(),
                )
            )
        else:
            await self.bot.respond_error(ctx, "Auto-Responder was not modified.")


def setup(bot):
    bot.add_cog(AutoResponder(bot))
