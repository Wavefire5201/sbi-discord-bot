import discord
from discord.ext import commands
from utils import TOKEN, get_logger

logger = get_logger(__name__)
logger.info("Logging started")

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


# Bot events
@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
        print("Commands synced!")


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="for sustainability..."
        )
    )
    print(f"Logged in as {bot.user}")


@bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext, error: discord.DiscordException
):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.respond("This command can only be used in a server.")
    else:
        raise error


@bot.slash_command(name="help", description="help command")
async def help(ctx: discord.ApplicationContext):
    await ctx.respond("help command")


# Load cogs
cogs = ["recording", "ai"]
for cog in cogs:
    bot.load_extension(f"cogs.{cog}")

# Run the bot
bot.run(TOKEN)
