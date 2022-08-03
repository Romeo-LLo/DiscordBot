import discord
import asyncio
from dbmanager import DatabaseManager
import matplotlib.pyplot as plt
from discord.ext import commands
from datetime import datetime
import os

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
    game_result_name = f'waited丨{game_name} result'
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
        name=f'{game_name} upload',
        overwrites=game_text_channel_overwrites,
        category=game_category
    )
    game_result_text_channel = await guild.create_text_channel(
        name=game_result_name,
        overwrites=game_result_text_channel_overwrites,
        category=game_reult_category
    )
    promptResultImg = discord.Embed(title=f"{game_name} result", description="Please upload the image of game result")
    promptResultImg.add_field(name="Note", value="File type should be jpg, png or jpeg", inline=False)

    showResultImg = discord.Embed(title=f"{game_name} result", description=f"The result image can be seen once players in {game_name} upload")
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
    db_manager = DatabaseManager('discord_bot')
    count = db_manager.count_game_collection()
    # result_channels = game_result_category.channels
    # number = len(result_channels) + 1
    return f'Game {count+1}'
     


async def delay_delete_channel(time_in_sec: int, channel: discord.channel) -> None:
    await channel.send(f'This channel will be closed in {time_in_sec} seconds.')
    await asyncio.sleep(time_in_sec)
    await channel.delete()   
    
async def wait_for_double_check_and_update_db(client: discord.client, unchecked_channel: discord.TextChannel, game_document: dict) -> None:
    game_players = game_document['player_list']
    score_list = []
    for player in game_players:
        await unchecked_channel.send(f"What is the score of {player}?")

        score = await client.wait_for("message")

        score_list.append(int(score.content))
        game_document['player_info'][player]['score'] = score.content

    highest_score = max(score_list)
    winner_index = [score_list.index(highest_score)]
    for i in range(len(score_list)):
        if i in winner_index:
            game_document['player_info'][game_players[i]]['status'] = 'win'
        else:
            game_document['player_info'][game_players[i]]['status'] = 'lose'
    game_name = game_document['game']
    db_manager = DatabaseManager('discord_bot')
    db_manager.replace_game_document(game_name, game_document)
    recorded_game_result_channel_name = f'recorded丨{game_name}-result'
    await unchecked_channel.send(f"Score has been recorded!")
    await unchecked_channel.edit(name=recorded_game_result_channel_name)
    
             
def get_sorted_member_index(members: list[discord.Member]) -> list:
    joined_time = [member.joined_at for member in members]
    sorted_index = sorted(range(len(members)), key=lambda k: joined_time[k])
    return sorted_index

def save_game_info_to_db(game_name: str, game_players: list[discord.Member]) -> None:
    game_players_by_Name = [f"{member.name}#{member.discriminator}" for member in game_players]
    
    player_info = {}
    for player in game_players_by_Name:
        player_info[player] = {
            'score': None,
            'status': None         
        }
    game_document = {
        'game': game_name,
        'player_list': game_players_by_Name,
        'player_info': player_info           
        } 
        
    db_manager = DatabaseManager('discord_bot')
    db_manager.insert_game_document(game_document)


def extract_game_document_from_db(game_name: str) -> list:
    

    db_manager = DatabaseManager('discord_bot')
    game_document = db_manager.query_game_document(game_name)
    
    return game_document



def save_game_info_to_db(game_name: str, game_players: list[discord.Member]) -> None:
    game_players_by_Name = [f"{member.name}#{member.discriminator}" for member in game_players]
    
    player_info = []
    for player in game_players_by_Name:
        
        player_info.append({
            'player_name': player,
            'score': None,
            'status': None               
        })

    game_document = {
        'game': game_name,
        'player_list': game_players_by_Name,
        'player_info': player_info           
        } 
        
    db_manager = DatabaseManager('discord_bot')
    db_manager.insert_game_document(game_document)


def extract_game_document_from_db(game_name: str) -> list:
    

    db_manager = DatabaseManager('discord_bot')
    game_document = db_manager.query_game_document(game_name)
    
    return game_document

async def wait_for_double_check_and_update_db(client: discord.client, unchecked_channel: discord.TextChannel, game_document: dict) -> None:
    game_players = game_document['player_list']
    game_name = game_document['game']

    score_list = []
    for player in game_players:
        await unchecked_channel.send(f"What is the score of {player}?")
        def check(m):
            return m.channel == unchecked_channel
        score = await client.wait_for("message", check=check)
        score_list.append(int(score.content))
        # game_document['player_info'][player]['score'] = score.content

    highest_score = max(score_list)
    winner_index = [score_list.index(highest_score)]
    rank_score_list = []
    for i in range(len(score_list)):
        if i in winner_index:
            game_document['player_info'][i]['status'] = 'win'
            rank_score = score_look_up_table(score_list[i], 'win')
            game_document['player_info'][i]['score'] = rank_score
            rank_score_list.append(rank_score)

        else:
            game_document['player_info'][i]['status'] = 'lose'
            rank_score = score_look_up_table(score_list[i], 'lose')
            game_document['player_info'][i]['score'] = rank_score
            rank_score_list.append(rank_score)



    db_manager = DatabaseManager('discord_bot')
    db_manager.replace_game_document(game_name, game_document)
    recorded_game_result_channel_name = f'recorded丨{game_name}-result'
    await unchecked_channel.send(f"Score has been recorded!")
    await unchecked_channel.edit(name=recorded_game_result_channel_name)
    await post_score_result(client, game_players, game_name, rank_score_list)

    
    
    
def score_look_up_table(score: int, win_or_lose: str) -> int:
    win_rank_score = [35, 30, 30, 25, 25, 20, 20, 15, 15, 15, 15, 10, 5]
    lose_rank_score = [-10, -10, -15, -15, -20, -20, -25, -25, -30, -30, -30, -30, -35]
    rank = score // 100
    
    if rank < 11:
        if win_or_lose == 'win':
            rank_score = win_rank_score[rank]
        if win_or_lose == 'lose':
            rank_score = lose_rank_score[rank]
    elif rank >= 11 and rank < 16:
        if win_or_lose == 'win':
            rank_score = win_rank_score[-2]
        if win_or_lose == 'lose':
            rank_score = lose_rank_score[-2]
    elif rank >= 16:
        if win_or_lose == 'win':
            rank_score = win_rank_score[-1]
        if win_or_lose == 'lose':
            rank_score = lose_rank_score[-1]
    else:
        rank_score = 0
        
    return rank_score
        
        
async def display_scoreboard(channel: discord.channel):
    
    db_manager = DatabaseManager('discord_bot')
    score_board = db_manager.show_score_board()     
    player = []
    total_score = []
    for each in score_board:
        player.append(each['_id'])
        total_score.append(each['total_score'])

    scoreboard = 'scoreboard.png'
    now = datetime.now()
    now = now.replace(microsecond = 0)        
    fig = plt.figure(figsize = (10, 5))
    plt.bar(player, total_score, width = 0.1)
    plt.xlabel("Player")
    plt.ylabel("Total score")
    plt.title("Score board ")
    plt.savefig(scoreboard)
    
    board_file=discord.File(scoreboard)
    baord = discord.Embed(title=f'Score board', description=f'Updated time: {now}')
    baord.set_image(url=f"attachment://{scoreboard}")
    await channel.send(embed=baord, file=board_file)
    
    if os.path.exists(scoreboard):
        os.remove(scoreboard)


async def post_score_result(client, game_players, game_name, rank_score_list):
    db_manager = DatabaseManager('discord_bot')
    guild = client.get_guild(994513374606004276) 
    score_channel = discord.utils.get(guild.text_channels, name='score')

    scoreResult = discord.Embed(title=f'Ranked Scoring System', description=game_name)

    for i, player in enumerate(game_players):
        total_score = db_manager.extract_player_score(player)
        for score in total_score:
            total_score = score['total_score']  
        rankscore = rank_score_list[i]
        if rankscore >= 0:
            add_or_minus = '+'
        else:
            add_or_minus = '-'

        scoreResult.add_field(name=f"Player {i+1}", value=f'<@{player}> {add_or_minus}{abs(rankscore)} [{total_score - rankscore} -> {total_score}]', inline=False) 

    await score_channel.send(embed=scoreResult)

