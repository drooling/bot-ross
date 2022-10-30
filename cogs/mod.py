# -*- coding: utf-8 -*-


import discord
from discord.ext import commands


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @discord.slash_command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: discord.ApplicationContext, cog: str):
        self.bot.reload_extension(cog)
        await self.bot.respond_success(ctx, "reloaded")

    @discord.slash_command(
        name="emojisteal",
        description="Steal an emoji from another server and upload it to yours",
    )
    @discord.option(
        name="emoji", type=str, description="The emoji to steal of course."
    )
    @discord.default_permissions(manage_emojis=True)
    @discord.guild_only()
    async def emojisteal(self, ctx: discord.ApplicationContext, emoji: str):
        emoji = await (commands.PartialEmojiConverter()).convert(ctx, emoji)
        new = await ctx.guild.create_custom_emoji(
            name=str(emoji.name),
            image=(await emoji.read()),
            reason="Emoji steal",
        )
        await ctx.respond(f"{new.name} was added to this server {new}")

def setup(bot):
    bot.add_cog(Mod(bot))
