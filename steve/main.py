import discord
from discord.ext import commands
from utils import get_logger
from utils.config import TOKEN

logger = get_logger(__name__)
logger.info("Logging started")

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


# Bot events
@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
        logger.info("Commands synced!")


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="for sustainability..."
        )
    )
    logger.info(f"Logged in as {bot.user}")


@bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext, error: discord.DiscordException
):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.respond("This command can only be used in a server.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond(
            "You do not have permission to use this command.", ephemeral=True
        )
    else:
        logger.error(f"Error occurred: {error}")
        raise error


# Load cogs
cogs = ["recording", "ai_", "utility", "admin", "meetings"]
for cog in cogs:
    bot.load_extension(f"cogs.{cog}")

# Run the bot
bot.run(TOKEN)
