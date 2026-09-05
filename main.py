import os
import asyncio

import discord
from discord.ext import commands

import config

intents = discord.Intents.default()
intents.message_content = True   # needed to read prefix commands
intents.members = True           # needed for role/member lookups
intents.emojis_and_stickers = True

bot = commands.Bot(
    command_prefix=config.PREFIXES,
    intents=intents,
    help_command=commands.DefaultHelpCommand(),
)


@bot.check
async def developer_only(ctx: commands.Context) -> bool:
    """Global check — every single command is restricted to the developer."""
    return ctx.author.id == config.DEVELOPER_ID


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print(f"Prefixes: {', '.join(config.PREFIXES)}")
    print(f"Developer-only ID: {config.DEVELOPER_ID}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    # Anyone who isn't the developer just gets silently ignored.
    if isinstance(error, commands.CheckFailure):
        return
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Bad argument: {error}")
        return
    if isinstance(error, discord.Forbidden):
        await ctx.send("⚠️ I don't have permission to do that (check my role position/permissions).")
        return

    print(f"Unhandled error in command '{ctx.command}': {error!r}")
    await ctx.send(f"⚠️ Error: `{error}`")


EXTENSIONS = (
    "cogs.channels",
    "cogs.roles",
    "cogs.embeds",
    "cogs.emojis",
)


async def main():
    async with bot:
        for ext in EXTENSIONS:
            await bot.load_extension(ext)

        token = os.environ.get("APP_TOKEN")
        if not token:
            raise RuntimeError(
                "APP_TOKEN environment variable is not set. "
                "In GitHub, set it under Settings → Secrets and variables → Actions."
            )
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
