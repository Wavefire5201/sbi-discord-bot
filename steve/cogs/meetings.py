import discord
from ai import get_transcription
from discord.ext import commands
from utils import get_logger

get_logger(__name__)


class Meetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="transcript", description="View the transcript of a meeting!"
    )
    async def transcript(self, ctx: discord.ApplicationContext, id: str):
        transcript = await get_transcription(id)

        if not transcript:
            await ctx.respond("No transcript found for this meeting.")
            return

        max_content_length = 2000 - 6  # Account for ``` ```

        if len(transcript) <= max_content_length:
            await ctx.respond(f"```{transcript}```")
        else:
            chunks = []
            for i in range(0, len(transcript), max_content_length):
                chunks.append(transcript[i : i + max_content_length])

            await ctx.respond(f"```{chunks[0]}```")

            for chunk in chunks[1:]:
                await ctx.followup.send(f"```{chunk}```")


def setup(bot):
    bot.add_cog(Meetings(bot))
