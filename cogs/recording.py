import logging

import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Recording(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connections = {}

    @commands.slash_command(
        name="record", description="Join the voice channel and start recording"
    )
    @commands.guild_only()
    async def record(self, ctx: discord.ApplicationContext):
        voice = ctx.author.voice

        if not voice:
            embed = discord.Embed(
                title="❌ Not in Voice Channel",
                description="You need to be in a voice channel to start recording!",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed)
            return

        vc = (
            await voice.channel.connect()
        )  # Connect to the voice channel the author is in.
        self.connections.update(
            {ctx.guild.id: vc}
        )  # Updating the cache with the guild and channel.

        vc.start_recording(
            discord.sinks.MP3Sink(),  # The sink type to use.
            self.once_done,  # What to do once done.
            ctx.channel,  # The channel to disconnect from.
        )
        embed = discord.Embed(
            title="🎙️ Recording Started",
            description=f"Started recording in {voice.channel.name}!",
            color=discord.Color.green(),
        )
        embed.add_field(name="🛑 Stop Command", value="`/stop_recording`", inline=False)
        await ctx.respond(embed=embed)

    async def once_done(
        self, sink: discord.sinks.MP3Sink, channel: discord.TextChannel, *args
    ):  # Our voice client already passes these in.
        recorded_users = [  # A list of recorded users
            f"<@{user_id}>" for user_id, audio in sink.audio_data.items()
        ]
        await sink.vc.disconnect()  # Disconnect from the voice channel.
        files = [
            discord.File(audio.file, f"{user_id}.{sink.encoding}")
            for user_id, audio in sink.audio_data.items()
        ]  # List down the files.
        embed = discord.Embed(
            title="🎙️ Recording Complete",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="👥 Recorded Users",
            value=", ".join(recorded_users) if recorded_users else "No users recorded",
            inline=False,
        )
        embed.add_field(
            name="📁 Files",
            value=f"{len(files)} audio file(s)",
            inline=True,
        )
        embed.set_footer(
            text=f"Recording finished at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        await channel.send(embed=embed, files=files)

    @commands.slash_command(name="stop_recording", description="Stop recording audio")
    @commands.guild_only()
    async def stop_recording(self, ctx: discord.ApplicationContext):
        # Check if the guild is in the cache.
        if ctx.guild.id in self.connections:
            vc = self.connections[ctx.guild.id]
            # Stop recording, and call the callback (once_done).
            vc.stop_recording()
            # Remove the guild from the cache.
            del self.connections[ctx.guild.id]
            await ctx.delete()
        else:
            embed = discord.Embed(
                title="❌ Not Recording",
                description="I am currently not recording in this server.",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Recording(bot))
