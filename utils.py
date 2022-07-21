from ntpath import join
from pickle import FALSE
from unicodedata import category
import discord
import os
from dotenv import load_dotenv

async def _get_category(guild: discord.Guild, CATEGORY_NAME: str) -> discord.CategoryChannel:
    """
    Return a category.
    """
    for category in guild.categories:
        if category.name == CATEGORY_NAME:
            return category

    return await _create_category(guild, CATEGORY_NAME)


async def _create_category(guild: discord.Guild, CATEGORY_NAME: str) -> discord.CategoryChannel:
    """Create a new category and return it."""
    # log.info("Creating a new code jam category.")

    category_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True), 
        
    }

    category = await guild.create_category_channel(
        CATEGORY_NAME,
        overwrites=category_overwrites
        )
    
    return category
        


async def create_team_channel_and_move_member(guild: discord.Guild, team_members: list[discord.Member], CATEGORY_NAME: str) -> None:
    """Create the team's voice channel. The channel will be in a game room hub category"""

    # Get permission overwrites and category

    team_category = await _get_category(guild, CATEGORY_NAME)
    
    team_name = await create_team_name(team_category)
    team_role = await guild.create_role(name="{} role".format(team_name))
    
    team_channel_overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False),
        team_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    # Create a voice channel for the team
    team_channel = await guild.create_voice_channel(
        name=team_name,
        overwrites=team_channel_overwrites,
        category=team_category
    )
    
    for member in team_members:
        await member.add_roles(team_role)
        await member.move_to(team_channel)

    
    
async def create_team_name(team_category: discord.CategoryChannel) -> str:
    channels = team_category.channels
    if channels == None:
        return 'Team 1'
    
    else:

        existed_channel = [channel.name.split()[-1] for channel in channels]
        existed_channel.sort()

        for i in range(len(existed_channel)):
            if int(existed_channel[i]) > (i + 1):
                return "Team {}".format(i+1)

        return "Team {}".format(len(existed_channel)+1)            
             

        