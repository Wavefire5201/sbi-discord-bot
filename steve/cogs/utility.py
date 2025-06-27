import discord
from discord.ext import commands
from utils import get_logger

get_logger(__name__)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help", description="help command")
    async def help(self, ctx: discord.ApplicationContext):
        await ctx.respond("help command")


def setup(bot):
    bot.add_cog(Utility(bot))
