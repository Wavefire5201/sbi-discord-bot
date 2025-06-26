import discord
from db import Person, create_person
from discord.ext import commands
from utils import get_logger

get_logger(__name__)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help", description="help command")
    async def help(self, ctx: discord.ApplicationContext):
        await ctx.respond("help command")

    @commands.slash_command(name="add_member", description="Add SBI member to DB")
    @commands.has_permissions(administrator=True)
    async def add_member(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        eid: str,
        email: str,
    ):
        if not member.nick:
            await ctx.respond(
                "Please make sure the member has their nickname set as their name!"
            )
            return

        await create_person(
            Person(discord_id=member.id, name=member.nick, email=email, eid=eid)
        )
        await ctx.respond(
            f"Added {member.name} ({member.nick}) to the SBI member's DB."
        )

    @commands.slash_command(
        name="list_members", description="List current SBI members in DB"
    )
    @commands.has_permissions(administrator=True)
    async def list_members(self, ctx: discord.ApplicationContext):
        await ctx.respond("wip")

    @commands.slash_command(
        name="check_member", description="Check if a member is in the DB"
    )
    @commands.has_permissions(administrator=True)
    async def check_member(
        self, ctx: discord.ApplicationContext, member: discord.Member
    ):
        await ctx.respond(f"<@{member.id}>")


def setup(bot):
    bot.add_cog(Utility(bot))
