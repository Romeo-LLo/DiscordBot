from ntpath import join
from pickle import FALSE
from unicodedata import category
import discord
import os
from dotenv import load_dotenv
import asyncio
from dbmanager import DatabaseManager


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
    """Create the team's voice channel. The channel will be in some category"""

    # Get permission overwrites and category
    team_category = await _get_category(guild, CATEGORY_NAME)
    team_name = await create_team_name_filling_gap(team_category)
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

    
    
         
             
async def create_game_channel_and_move_member(guild: discord.Guild, game_players: list[discord.Member], CATEGORY_NAME: str, result_CATEGORY_NAME) -> None:
    """Create the game's voice channel."""

    # Get permission overwrites and category
    game_category = await _get_category(guild, CATEGORY_NAME)
    game_reult_category = await _get_category(guild, result_CATEGORY_NAME)
    game_name = await create_game_name_successive(game_reult_category)
    game_result_name = f'waiting丨{game_name} result'
    game_role = await guild.create_role(name="{} role".format(game_name))
    
    game_channel_overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False),
        game_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    game_text_channel_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        game_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    game_result_text_channel_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
    }

    # Create a voice channel for the game
    game_channel = await guild.create_voice_channel(
        name=game_name,
        overwrites=game_channel_overwrites,
        category=game_category
    )
    game_text_channel = await guild.create_text_channel(
        name=f'{game_name} result',
        overwrites=game_text_channel_overwrites,
        category=game_category
    )
    game_result_text_channel = await guild.create_text_channel(
        name=game_result_name,
        overwrites=game_result_text_channel_overwrites,
        category=game_reult_category
    )
    promptResultImg = discord.Embed(title="Game 1 result", description="Please upload the image of game result")
    promptResultImg.add_field(name="Note", value="File type should be jpg, png or jpeg", inline=False)

    showResultImg = discord.Embed(title="Game 1 result", description=f"The result image can be seen once players in {game_name} upload")
    showResultImg.add_field(name="Note", value="The double check action by admin will be carried out", inline=False)

    await game_text_channel.send(embed=promptResultImg)
    await game_result_text_channel.send(embed=showResultImg)

    for member in game_players:
        await member.add_roles(game_role)
        await member.move_to(game_channel)
        
    save_game_info_to_db(game_name, game_players)


async def create_team_name_filling_gap(team_category: discord.CategoryChannel) -> str:
    channels = team_category.channels

    if len(channels) == 0:
        return 'Team 1'  
    else:
        existed_channel = [channel.name.split()[-1] for channel in channels]
        existed_channel.sort()

        for i in range(len(existed_channel)):
            if int(existed_channel[i]) > (i + 1):
                return "Team {}".format(i+1)

        return "Team {}".format(len(existed_channel)+1)   

async def create_game_name_successive(game_result_category: discord.CategoryChannel) -> str:
    result_channels = game_result_category.channels
    number = len(result_channels) + 1
    return f'Game {number}'
    # if len(channels) == 0:
    #     return 'Game 1'
    # else:
    #     existed_channel = [channel.name.split()[-1] for channel in channels]
    #     existed_channel = [int(channel.name.split()[-1]) for channel in channels]
    #     last_team = max(existed_channel)
    #     return "Game {}".format(last_team + 1)            


async def delay_delete_channel(time_in_sec: int, channel: discord.channel) -> None:
    await channel.send(f'This channel will be closed in {time_in_sec} seconds.')
    await asyncio.sleep(time_in_sec)
    await channel.delete()    
             
def get_sorted_member_index(members: list[discord.Member]) -> list:
    joined_time = [member.joined_at for member in members]
    sorted_index = sorted(range(len(members)), key=lambda k: joined_time[k])
    return sorted_index

def save_game_info_to_db(game_name: str, game_players: list[discord.Member]) -> None:
    game_players_by_Name = [f"{member.name}#{member.discriminator}" for member in game_players]
    
    players_info = {}
    for player in game_players_by_Name:
        players_info[player] = {
            'score': None,
            'status': None         
        }
        
    game_document = {
        'game': game_name,
        'players': players_info           
        } 
    
    print(game_document)
    
    
    db_manager = DatabaseManager('discord_bot')
    db_manager.insert_game_document(game_document)

    