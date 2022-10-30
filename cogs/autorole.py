import discord
from discord.ext import commands


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def assign_autoroles(self, member: discord.Member):
        async for record in self.bot.database.auto_role.find(
            {"guild": str(member.guild.id)}
        ):
            await member.add_roles(
                member.guild.get_role(int(record.get("role"))), reason="Auto-Role"
            )

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member):
        await self.assign_autoroles(member)

    config = discord.SlashCommandGroup(
        "autorole",
        "Automatically assign a member role(s) upon joining your server.",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    @config.command(name="view", description="View roles to be assigned upon joining")
    @discord.guild_only()
    async def view_autoroles(self, ctx: discord.ApplicationContext):
        autoroles = []
        async for record in self.bot.database.auto_role.find(
            {"guild": str(ctx.guild.id)}
        ):
            autoroles.append(ctx.guild.get_role(int(record.get("role"))).mention)
        embed = discord.Embed(title="Ross Auto-Role", color=discord.Color.dark_grey())
        if len(autoroles) > 0:
            embed.description = (
                " and ".join(autoroles)
            ) + " will be assigned upon joining."
        else:
            embed.description = (
                "There are no Auto-Role(s) setup. To add some use `/autorole add`"
            )
        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @config.command(name="add", description="Add a role to be assigned upon joining")
    @discord.option("role", type=discord.Role, description="Role to be assigned")
    @discord.guild_only()
    async def add_autorole(self, ctx: discord.ApplicationContext, role: discord.Role):
        await self.bot.database.auto_role.insert_one(
            {"guild": str(ctx.guild.id), "role": str(role.id)}
        )
        await ctx.respond(
            embed=discord.Embed(
                description=f"{role.mention} will now be assigned upon joining.",
                color=discord.Color.dark_grey(),
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @config.command(name="remove", description="Remove an Auto-Role")
    @discord.option("role", type=discord.Role, description="Role to be assigned")
    @discord.guild_only()
    async def add_autorole(self, ctx: discord.ApplicationContext, role: discord.Role):
        ack = await self.bot.database.auto_role.delete_one({"role": str(role.id)})
        embed = discord.Embed(color=discord.Color.dark_grey())
        if not ack.deleted_count > 0:
            embed.description = "That role was not an Auto-Role"
        else:
            embed.description = (
                f"{role.mention} will no longer be assigned upon joining."
            )
        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions.none())


def setup(bot):
    bot.add_cog(AutoRole(bot))
