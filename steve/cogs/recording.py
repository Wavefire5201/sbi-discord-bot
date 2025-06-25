import asyncio
import traceback
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands, tasks
from utils import get_logger

logger = get_logger(__name__)


def unix_time_now() -> int:
    return round(datetime.now().timestamp())


class RecordingView(discord.ui.View):
    def __init__(self, _stop_recording):
        super().__init__()
        self._stop_recording = _stop_recording

    async def disable_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Stop Recording", style=discord.ButtonStyle.red)
    async def stop_recording_callback(self, button, interaction: discord.Interaction):
        await self._stop_recording(interaction)
        await self.disable_buttons()
        await interaction.message.edit(view=self)


class Recording(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connections = {}
        self.recording_tasks = {}
        self.max_recording_duration = 3600 * 5  # 5 hour max recording
        self.status_update_task.start()

    @commands.slash_command(
        name="join",
        description="Join the voice channel and start recording",
    )
    @commands.guild_only()
    async def join(self, ctx: discord.ApplicationContext):
        voice = ctx.author.voice

        if not voice:
            embed = discord.Embed(
                title="Not in Voice Channel",
                description="You need to be in a voice channel to start recording!",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if ctx.guild.id in self.connections:
            embed = discord.Embed(
                title="Already Recording",
                description="Already recording in this server! Use `/stop` first.",
                color=discord.Color.orange(),
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            # Defer the response since connection might take time
            await ctx.defer()

            # Connect to voice channel
            vc = await voice.channel.connect(reconnect=True, timeout=10.0)

            # Create initial status embed
            start_time = unix_time_now()
            status_embed = self._create_status_embed(start_time, voice.channel.id)
            status_message = await ctx.followup.send(
                embed=status_embed, view=RecordingView(self._stop_recording)
            )

            # Store connection
            self.connections[ctx.guild.id] = {
                "voice_client": vc,
                "channel": ctx.channel,
                "start_time": start_time,
                "users_recorded": set(),
                "status_message": status_message,
                "voice_channel_id": voice.channel.id,
            }

            # Create a custom sink with better error handling
            sink = SafeWaveSink()

            # Play recording start sound
            await self._play_recording_start_sound(vc)

            # Start recording with timeout protection
            vc.start_recording(
                sink, self.recording_finished_callback, ctx.channel, ctx.guild.id
            )

            # Set up automatic timeout
            timeout_task = asyncio.create_task(
                self._auto_stop_recording(ctx.guild.id, self.max_recording_duration)
            )
            self.recording_tasks[ctx.guild.id] = timeout_task

            logger.info(
                f"Started alternative recording in guild {ctx.guild.id}, channel {voice.channel.name}"
            )

        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Connection Timeout",
                description="Failed to connect to voice channel (timeout)",
                color=discord.Color.red(),
            )
            await ctx.followup.send(embed=embed)
            logger.error(f"Timeout connecting to voice channel in guild {ctx.guild.id}")
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            logger.error(traceback.format_exc())
            embed = discord.Embed(
                title="Recording Failed",
                description=f"Failed to start recording: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.followup.send(embed=embed)
            # Clean up on error
            await self._cleanup_recording(ctx.guild.id)

    async def recording_finished_callback(self, sink, channel, guild_id, *args):
        """Callback when recording finishes"""
        try:
            logger.info(f"Recording finished for guild {guild_id}")

            # Cancel timeout task if it exists
            if guild_id in self.recording_tasks:
                self.recording_tasks[guild_id].cancel()
                del self.recording_tasks[guild_id]

            connection_info = self.connections.get(guild_id)
            if not connection_info:
                logger.warning(f"No connection info found for guild {guild_id}")
                return

            # Check if we have any audio data
            if not hasattr(sink, "audio_data") or not sink.audio_data:
                embed = discord.Embed(
                    title="🎙️ Recording Complete",
                    description="Recording finished, but no audio was captured. Make sure users are speaking!",
                    color=discord.Color.orange(),
                )
                await channel.send(embed=embed)
                logger.info(f"No audio data captured for guild {guild_id}")
                return

            # Process audio files
            files = []
            recorded_users = []

            for user_id, audio_data in sink.audio_data.items():
                try:
                    if audio_data and hasattr(audio_data, "file") and audio_data.file:
                        # Reset file position
                        audio_data.file.seek(0)

                        # Check if file has content
                        file_size = len(audio_data.file.read())
                        audio_data.file.seek(0)

                        if file_size > 0:
                            filename = f"recording_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{sink.encoding}"
                            files.append(discord.File(audio_data.file, filename))
                            recorded_users.append(f"<@{user_id}>")
                            logger.info(
                                f"Created audio file for user {user_id}, size: {file_size} bytes"
                            )
                        else:
                            logger.warning(f"Empty audio file for user {user_id}")

                except Exception as e:
                    logger.error(f"Error processing audio for user {user_id}: {e}")
                    continue

            # Send results
            if files:
                duration = datetime.now() - datetime.fromtimestamp(
                    connection_info["start_time"]
                )
                duration_str = str(duration).split(".")[0]  # Remove microseconds

                embed = discord.Embed(
                    title="🎙️ Recording Complete!", color=discord.Color.green()
                )
                embed.add_field(name="⏱️ Duration", value=duration_str, inline=True)
                embed.add_field(
                    name="📁 Files", value=f"{len(files)} audio file(s)", inline=True
                )
                embed.add_field(
                    name="👥 Recorded Users",
                    value=", ".join(recorded_users),
                    inline=False,
                )
                embed.set_footer(
                    text=f"Recording finished at <t:{datetime.now().timestamp()}:f>"
                )

                await channel.send(embed=embed, files=files)
                logger.info(f"Sent {len(files)} audio files for guild {guild_id}")
            else:
                embed = discord.Embed(
                    title="🎙️ Recording Complete",
                    description="Recording finished, but no valid audio files could be created. "
                    "This might happen if users weren't speaking or there were connection issues.",
                    color=discord.Color.orange(),
                )
                await channel.send(embed=embed)
                logger.warning(f"No valid audio files created for guild {guild_id}")

        except Exception as e:
            logger.error(f"Error in recording callback for guild {guild_id}: {e}")
            logger.error(traceback.format_exc())
            try:
                embed = discord.Embed(
                    title="Recording Error",
                    description=f"Recording finished, but there was an error processing the audio: {str(e)}",
                    color=discord.Color.red(),
                )
                await channel.send(embed=embed)
            except:
                logger.error("Failed to send error message to channel")
        finally:
            # Always clean up
            await self._cleanup_recording(guild_id)

    @commands.slash_command(name="stop", description="Stop the current recording")
    @commands.guild_only()
    async def stop(self, ctx: discord.ApplicationContext):
        if ctx.guild.id not in self.connections:
            embed = discord.Embed(
                title="Not Recording",
                description="Not currently recording in this server.",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await self._stop_recording(ctx)

    async def _stop_recording(self, ctx: discord.ApplicationContext):
        try:
            connection_info = self.connections[ctx.guild.id]
            vc = connection_info["voice_client"]

            # Stop recording
            vc.stop_recording()

            embed = discord.Embed(
                title="⏹️ Stopping Recording",
                description="Recording is being stopped and processed...",
                color=discord.Color.blue(),
            )
            await ctx.respond(embed=embed)
            logger.info(f"Manually stopped recording in guild {ctx.guild.id}")

        except Exception as e:
            logger.error(f"Error stopping recording in guild {ctx.guild.id}: {e}")
            embed = discord.Embed(
                title="Stop Error",
                description=f"Error stopping recording: {str(e)}",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed)
            # Force cleanup even if there was an error
            await self._cleanup_recording(ctx.guild.id)

    @commands.slash_command(name="status", description="Check recording status")
    @commands.guild_only()
    async def status(self, ctx: discord.ApplicationContext):
        if ctx.guild.id not in self.connections:
            embed = discord.Embed(
                title="Not Recording",
                description="Not currently recording in this server.",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        connection_info = self.connections[ctx.guild.id]
        status_embed = self._create_status_embed(
            connection_info["start_time"],
            connection_info["voice_channel_id"],
        )
        await ctx.respond(embed=status_embed)

    async def _auto_stop_recording(self, guild_id: int, duration: int):
        """Automatically stop recording after specified duration"""
        try:
            await asyncio.sleep(duration)

            if guild_id in self.connections:
                logger.info(
                    f"Auto-stopping recording for guild {guild_id} after {duration} seconds"
                )
                connection_info = self.connections[guild_id]
                vc = connection_info["voice_client"]
                vc.stop_recording()

                # Send timeout message
                try:
                    embed = discord.Embed(
                        title="Recording Timeout",
                        description=f"Recording automatically stopped after {duration // 60} minutes (max duration reached)",
                        color=discord.Color.orange(),
                    )
                    await connection_info["channel"].send(embed=embed)
                except:
                    logger.error(f"Failed to send timeout message for guild {guild_id}")

        except asyncio.CancelledError:
            logger.info(f"Auto-stop task cancelled for guild {guild_id}")
        except Exception as e:
            logger.error(f"Error in auto-stop task for guild {guild_id}: {e}")

    async def _cleanup_recording(self, guild_id: int):
        """Clean up recording resources"""
        try:
            # Cancel timeout task
            if guild_id in self.recording_tasks:
                self.recording_tasks[guild_id].cancel()
                del self.recording_tasks[guild_id]

            # Disconnect voice client
            if guild_id in self.connections:
                connection_info = self.connections[guild_id]
                vc = connection_info["voice_client"]

                if vc and vc.is_connected():
                    await vc.disconnect()
                    logger.info(f"Disconnected voice client for guild {guild_id}")

                del self.connections[guild_id]

        except Exception as e:
            logger.error(f"Error cleaning up recording for guild {guild_id}: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates to manage recordings"""
        # If bot is disconnected from voice channel, clean up recording
        if member == self.bot.user and before.channel and not after.channel:
            for guild_id, connection_info in list(self.connections.items()):
                if connection_info["voice_client"].channel == before.channel:
                    logger.info(
                        f"Bot disconnected from voice channel, cleaning up recording for guild {guild_id}"
                    )
                    await self._cleanup_recording(guild_id)

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        logger.info("Cleaning up all recordings on cog unload")
        self.status_update_task.cancel()
        for guild_id in list(self.connections.keys()):
            asyncio.create_task(self._cleanup_recording(guild_id))

    async def _play_recording_start_sound(self, voice_client):
        """Play the recording started sound effect"""
        try:
            # Get path relative to this file's location
            audio_path = (
                Path(__file__).parent.parent / "audio" / "recording_started.wav"
            )
            if audio_path.exists():
                # Create audio source
                audio_source = discord.FFmpegPCMAudio(str(audio_path))

                # Play the audio
                voice_client.play(audio_source)

                # Wait for audio to finish playing
                while voice_client.is_playing():
                    await asyncio.sleep(0.1)

                logger.info("Played recording start sound")
            else:
                logger.warning(f"Recording start sound file not found: {audio_path}")
        except Exception as e:
            logger.error(f"Error playing recording start sound: {e}")

    def _create_status_embed(
        self, start_time: int, voice_channel_id: int
    ) -> discord.Embed:
        """Create a status embed for the recording"""
        duration = datetime.now() - datetime.fromtimestamp(start_time)
        duration_str = str(duration).split(".")[0]  # Remove microseconds

        embed = discord.Embed(
            title="🔴 Recording...",
            color=discord.Color.green(),
            timestamp=datetime.fromtimestamp(start_time),
        )
        embed.add_field(
            name="**Started:**",
            value=f"<t:{start_time}:T> (<t:{start_time}:R>)",
            inline=False,
        )
        embed.add_field(name="**Duration:**", value=duration_str, inline=False)
        embed.add_field(
            name="**Channel:**", value=f"<#{voice_channel_id}>", inline=False
        )

        return embed

    @tasks.loop(seconds=1)
    async def status_update_task(self):
        """Update status embeds every second"""
        for guild_id, connection_info in list(self.connections.items()):
            try:
                if "status_message" in connection_info:
                    status_embed = self._create_status_embed(
                        connection_info["start_time"],
                        connection_info["voice_channel_id"],
                    )
                    await connection_info["status_message"].edit(embed=status_embed)
            except Exception as e:
                logger.error(f"Error updating status embed for guild {guild_id}: {e}")

    @status_update_task.before_loop
    async def before_status_update(self):
        """Wait until bot is ready before starting status updates"""
        await self.bot.wait_until_ready()


class SafeWaveSink(discord.sinks.MP3Sink):
    """A safer version of WaveSink with better error handling"""

    def __init__(self):
        super().__init__()
        self.encoding = "mp3"

    def write(self, data, user):
        """Override write method with error handling"""
        try:
            return super().write(data, user)
        except Exception as e:
            logger.error(f"Error writing audio data for user {user}: {e}")
            # Continue without crashing
            pass

    def cleanup(self):
        """Override cleanup with error handling"""
        try:
            return super().cleanup()
        except Exception as e:
            logger.error(f"Error during sink cleanup: {e}")


def setup(bot):
    bot.add_cog(Recording(bot))
