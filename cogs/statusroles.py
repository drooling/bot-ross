import contextlib
import difflib
import discord
from discord.errors import NotFound
from discord.ext import commands


class StatusRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def roles_complete(self, ctx: discord.AutocompleteContext):
        choices = await (
            self.bot.database.status_roles.find(
                {"guild": str(ctx.interaction.guild.id)}
            )
        ).to_list(length=None)
        if len(choices) < 25:
            return [
                f"[@{ctx.interaction.guild.get_role(int(r.get('role'))).name}] - {r.get('keyword')}"
                for r in choices
            ]
        else:
            if len(ctx.value) < 1:
                return ["Enter at least 1 character for autocompletion"]
            return difflib.get_close_matches(
                ctx.value,
                [
                    f"[@{ctx.interaction.guild.get_role(int(r.get('role'))).name}] - {r.get('keyword')}"
                    for r in choices
                ],
                cutoff=0.2,
            )

    @commands.Cog.listener("on_presence_update")
    async def status_roles(self, before: discord.Member, after: discord.Member):
        status = None
        for activity in after.activities:
            if activity.type == discord.ActivityType.custom:
                status = activity
        async for record in self.bot.database.status_roles.find(
            {"guild": str(after.guild.id)}
        ):
            if str(after.status) == str(discord.Status.offline):
                return
            else:
                with contextlib.suppress(TypeError, AttributeError):
                    if str(record.get("keyword")) in status.name:
                        await after.add_roles(
                            after.guild.get_role(int(record.get("role"))),
                            reason="Status roles",
                            atomic=True,
                        )
                    elif str(record.get("keyword")) not in status.name:
                        await after.remove_roles(
                            after.guild.get_role(int(record.get("role"))),
                            reason="Status roles",
                            atomic=True,
                        )

    statusroles = discord.SlashCommandGroup(
        "statusroles",
        "Automatically assign role(s) to a member if a keyword is in their status",
        checks=[commands.has_guild_permissions(administrator=True).predicate],
    )

    @statusroles.command(name="add", description="Add a new Status-Role")
    @discord.option(name="keyword", type=str, description="The keyword to match")
    @discord.option(
        name="role",
        type=discord.Role,
        description="The role to assign when the keyword is found",
    )
    @discord.guild_only()
    async def add_statusroles(
        self, ctx: discord.ApplicationContext, keyword: str, role: discord.Role
    ):
        ack = await self.bot.database.status_roles.insert_one(
            {"guild": str(ctx.guild.id), "keyword": keyword, "role": str(role.id)}
        )
        if ack.inserted_id:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"{role.mention} will be assigned to members upon finding `{keyword}` in their status.",
                    color=discord.Color.dark_grey(),
                ),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await self.bot.respond_error(ctx, "Status-Roles were not modified.")

    @statusroles.command(
        name="remove", description="Remove a keyword from the Status-Roles"
    )
    @discord.option(
        name="rule",
        type=str,
        description="The Status-Role to remove.",
        autocomplete=roles_complete,
    )
    @discord.guild_only()
    async def remove_statusroles(self, ctx: discord.ApplicationContext, rule: str):
        if rule.__contains__(" - "):
            keyword = rule.split(" - ")[1]
            role = discord.utils.find(
                lambda r: r.name == rule.split("[@", 1)[1].split("]", 1)[0],
                ctx.guild.roles,
            )
        ack = await self.bot.database.status_roles.delete_one(
            {"guild": str(ctx.guild.id), "keyword": keyword, "role": str(role.id)}
        )
        if ack.deleted_count > 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"{role.mention} will no longer be assigned.",
                    color=discord.Color.dark_grey(),
                ),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await self.bot.respond_error(ctx, "Status-Roles were not modified.")


def setup(bot):
    bot.add_cog(StatusRoles(bot))
