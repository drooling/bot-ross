import discord
import discord.utils
from discord.ext import commands


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        user_ids = [str(member.id) for member in message.mentions]
        user_ids.append(str(message.author.id))
        embeds = []
        async for record in self.bot.database.afk.find({"user": {"$in": user_ids}}):
            if int(record.get("user")) == message.author.id:
                await self.bot.database.afk.delete_one({"user": str(message.author.id)})
                return await message.reply(
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(), description="Welcome back !"
                    )
                )
            embeds.append(
                discord.Embed(
                    color=discord.Color.dark_grey(),
                    description=f"{message.guild.get_member(int(record.get('user'))).mention} is **AFK**.\n\n> {record.get('status')}",
                )
            )
        if len(embeds) > 0:
            await message.reply(
                embeds=embeds, allowed_mentions=discord.AllowedMentions.none()
            )

    @discord.slash_command(name="afk", description="Set AFK status")
    @discord.option(
        "status", type=str, description="AFK Status/Message", default="Be back soon !"
    )
    @discord.guild_only()
    async def set_afk(self, ctx: discord.ApplicationContext, status: str):
        await self.bot.database.afk.insert_one(
            {"user": str(ctx.author.id), "status": status}
        )
        embed = discord.Embed(
            description="Hope to see you again soon !", color=discord.Color.dark_grey()
        )
        await ctx.respond(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )


def setup(bot):
    bot.add_cog(AFK(bot))
