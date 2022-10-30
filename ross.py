import asyncio
import logging
import os
from datetime import datetime
import traceback

import discord
import motor.motor_asyncio
from discord.commands.context import ApplicationContext
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)


class Ross(discord.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        asyncio.run(self.startup())

        self.load_extension("cogs.afk")
        self.load_extension("cogs.fun")
        self.load_extension("cogs.mod")
        self.load_extension("cogs.info")
        self.load_extension("cogs.joindm")
        self.load_extension("cogs.automod")
        self.load_extension("cogs.antiraid")
        self.load_extension("cogs.autorole")
        self.load_extension("cogs.blacklist")
        self.load_extension("cogs.stickynick")
        self.load_extension("cogs.statusroles")
        self.load_extension("cogs.relationship")
        self.load_extension("cogs.autoresponder")

    async def startup(self):
        self.database = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017).ross

    async def on_application_command_completion(self, ctx: ApplicationContext):
        js = {
            "command": str(ctx.command.name),
            "args": ctx.selected_options,
            "time": int(datetime.now().timestamp()),
            "user": dict(ctx.user._user._to_minimal_user_json()),
        }
        logging.getLogger("discord.client").info("Command received: %s", js)

    async def on_application_command_error(
        self, interaction: ApplicationContext, exc: Exception
    ):
        if isinstance(exc, commands.CommandOnCooldown):
            return await self.respond_error(
                interaction,
                f"Slow down ! You need to wait {exc.retry_after:.2f} seconds to use that command again.",
            )
        elif isinstance(exc, commands.CheckFailure):
            return await self.respond_error(interaction, f"You are unable to use that command.")
        else:
            js = {
                "exception": exc,
                "command": str(interaction.command.name),
                "args": interaction.selected_options,
                "time": int(datetime.now().timestamp()),
            }
            logging.getLogger("discord.client").error("Error received: %s", js)
            interaction.command.reset_cooldown(interaction)
            return await self.respond_error(interaction, f"Something went wrong.\n```\n{exc.args[0]}\n```")

    async def respond_error(self, ctx, message):
        return await ctx.respond(
            embed=discord.Embed(
                color=discord.Color.dark_grey(), description="<:x_:1033585872102232104> - **{0}**".format(message)
            ),
            ephemeral=True,
        )

    async def respond_success(self, ctx, message, **kwargs):
        return await ctx.respond(
            embed=discord.Embed(
                color=discord.Color.dark_grey(), description="<:check:1033585829244837909> - **{0}**".format(message)
            ), 
            **kwargs
        )


Ross("/", intents=discord.Intents.all()).run(token=os.getenv("DISCORD_BOT_TOKEN"))
