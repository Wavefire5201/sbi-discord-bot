import discord
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN not set, not starting the bot.")

intents = discord.Intents.all()
bot = discord.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
        print("Commands synced!")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.slash_command(name="help", description="help command")
async def help(ctx: discord.ApplicationContext):
    await ctx.respond("help command")


@bot.slash_command(name="join", description="Join the current voice channel you're in!")
async def join(ctx: discord.ApplicationContext):
    if not isinstance(ctx.author, discord.Member):
        await ctx.respond("This command can only be used in a server!")
        return

    vc_state = ctx.author.voice
    if vc_state is None:
        await ctx.respond("You're not in a voice channel!")
        return

    voice_channel = vc_state.channel
    if voice_channel is None:
        await ctx.respond("Could not find your voice channel!")
        return

    await voice_channel.connect()
    await ctx.respond(f"I've connected to your voice channel {voice_channel.id}")


@bot.slash_command(name="leave", description="Leave the voice channel")
async def leave(ctx: discord.ApplicationContext):
    if not isinstance(ctx.author, discord.Member):
        await ctx.respond("This command can only be used in a server!")
        return

    # Check if the bot is connected to a voice channel
    voice_client = ctx.guild.voice_client
    if voice_client is None:
        await ctx.respond("I'm not connected to a voice channel!")
        return

    # Disconnect from the voice channel
    await voice_client.disconnect()
    await ctx.respond("Left the voice channel!")


bot.run(TOKEN)
