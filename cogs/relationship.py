import contextlib
from datetime import datetime

import discord
import humanize
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType


class ConfirmOrDeny(discord.ui.View):
    def __init__(self, proposed: discord.Member = None):
        super().__init__(timeout=60)
        self.proposed = proposed or None
        self.accepted = False

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def accept_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if (self.proposed is not None) and (interaction.user.id != self.proposed.id):
            await interaction.response.send_message(
                embed=discord.Embed(
                    color=discord.Color.dark_grey(),
                    description="Stay out of other people's relationships. \U0001F612",
                ),
                ephemeral=True,
            )
        else:
            self.accepted = True
            await interaction.message.edit(view=None)
            self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def deny_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if interaction.user.id != self.proposed.id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    color=discord.Color.dark_grey(),
                    description="Stay out of other people's relationships. \U0001F612",
                ),
                ephemeral=True,
            )
        else:
            self.accepted = False
            await interaction.message.edit(view=None)
            self.stop()


class Relationship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="marry", description="Marriage <3")
    @discord.option(
        name="spouse", type=discord.Member, description="Who you wanna propose too"
    )
    @discord.guild_only()
    @commands.cooldown(1, 75, BucketType.member)
    async def marry(self, ctx: discord.ApplicationContext, spouse: discord.Member):
        if spouse == ctx.author:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.respond_error(
                ctx, "Why would you want to marry yourself? \U0001F928"
            )
        elif spouse.bot:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.respond_error(
                ctx, "Why you tryna marry a bot? \U0001F928"
            )
        existing = await self.bot.database.relationships.find_one(
            {"relationship.couple": str(ctx.author.id)}
        )
        if existing is not None:
            couple = set(existing.get("relationship").get("couple"))
            couple.discard(str(ctx.author.id))
            partner = await self.bot.fetch_user(int(couple.pop()))
            if partner.id == spouse.id:
                ctx.command.reset_cooldown(ctx)
                return await self.bot.respond_error(
                    ctx,
                    f"You two are already married. \U0001F926",
                )
            ctx.command.reset_cooldown(ctx)
            return await self.bot.respond_error(
                ctx,
                f"At least divorce {partner.mention} first. \U0001F62C",
            )
        existing = await self.bot.database.relationships.find_one(
            {"relationship.couple": str(spouse.id)}
        )
        if existing is not None:
            couple = set(existing.get("relationship").get("couple"))
            couple.discard(str(spouse.id))
            partner = couple.pop()
            ctx.command.reset_cooldown(ctx)
            return await self.bot.respond_error(
                ctx,
                f"{spouse.mention} is already married to **{await self.bot.fetch_user(int(partner))}**. Yikers. \U0001F925",
            )
        proposal = ConfirmOrDeny(spouse)
        await ctx.respond(
            content=spouse.mention,
            embed=discord.Embed(
                color=discord.Color.dark_grey(),
                description=f"Do you, {spouse.mention}, take {ctx.author.mention}'s hand in marriage?",
            ),
            view=proposal,
        )
        await proposal.wait()
        if proposal.accepted:
            ack = await self.bot.database.relationships.insert_one(
                {
                    "relationship": {
                        "couple": [str(ctx.author.id), str(spouse.id)],
                        "time": datetime.now(),
                    }
                }
            )
            if ack.inserted_id:
                return await ctx.respond(
                    content=ctx.author.mention,
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        description=f"\U0001F973 {spouse.mention} SAID YES!!! {ctx.author.mention} and {spouse.mention} are now married! \U0001F389\U0001F389\U0001F389",
                    ),
                )
        else:
            return await ctx.respond(
                embed=discord.Embed(
                    color=discord.Color.dark_grey(),
                    description=f"damn.",
                )
            )

    @discord.slash_command(name="divorce", description="</3")
    @discord.guild_only()
    @commands.cooldown(1, 75, BucketType.member)
    async def divorce(self, ctx: discord.ApplicationContext):
        existing = await self.bot.database.relationships.find_one(
            {"relationship.couple": str(ctx.author.id)}
        )
        if existing is None:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.respond_error(
                ctx,
                f"You aren't even married. \U0001F62C",
            )
        couple = set(existing.get("relationship").get("couple"))
        couple.discard(str(ctx.author.id))
        partner = await self.bot.fetch_user(int(couple.pop()))
        signed = ConfirmOrDeny()
        await ctx.respond(
            content=ctx.author.mention,
            embed=discord.Embed(
                color=discord.Color.dark_grey(),
                description=f"Are you sure you want to divorce **{partner}**?",
            ),
            view=signed,
        )
        await signed.wait()
        if signed.accepted:
            ack = await self.bot.database.relationships.delete_one(
                {"relationship.couple": [str(ctx.author.id), str(partner.id)]}
            )
            if ack.deleted_count > 0:
                with contextlib.suppress(discord.Forbidden):
                    await partner.send(
                        embed=discord.Embed(
                            color=discord.Color.dark_grey(),
                            description=f"You are now divorced. \U0001F622",
                        ),
                    )
                return await ctx.respond(
                    content=ctx.author.mention,
                    embed=discord.Embed(
                        color=discord.Color.dark_grey(),
                        description=f"You are now divorced. \U0001F622",
                    ),
                )
        else:
            return await ctx.respond(
                embed=discord.Embed(
                    color=discord.Color.dark_grey(),
                    description=f"Woah, close call.",
                )
            )

    @discord.slash_command(
        name="spouse", description="Show off who you're married to <3"
    )
    @discord.guild_only()
    @commands.cooldown(1, 7, BucketType.member)
    async def spouse(self, ctx: discord.ApplicationContext):
        existing = await self.bot.database.relationships.find_one(
            {"relationship.couple": str(ctx.author.id)}
        )
        if existing is None:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.respond_error(
                ctx,
                f"You aren't even married. \U0001F62C",
            )
        couple = set(existing.get("relationship").get("couple"))
        couple.discard(str(ctx.author.id))
        partner = await self.bot.fetch_user(int(couple.pop()))
        await ctx.respond(
            embed=discord.Embed(
                color=discord.Color.dark_grey(),
                description=f"\U0001F497 {ctx.author.mention} has been married to **{partner}** since **{humanize.naturaltime(existing.get('relationship').get('time'))}**",
            )
        )


def setup(bot):
    bot.add_cog(Relationship(bot))
