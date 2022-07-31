import discord
import os
from dotenv import load_dotenv
from utils import * 
from utils import _get_category
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# intents = discord.Intents.default()  # Allow the use of custom intents
# intents.members = True
client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    # After the game ends, each game text channel must upload a result image  
    if message.channel.category.name == 'Game hub':
        guild = client.get_guild(994513374606004276) 
        image_uploaded = message.attachments[0]
        img_type = ['.jpg','.png','.jpeg']
        for type in img_type:

            if image_uploaded.filename.endswith(type):
                game_num = ''.join(s for s in message.channel.name if s.isdigit())

                waited_game_result_channel_name = f'waited丨game-{game_num}-result'
                waited_game_result_channel = discord.utils.get(guild.text_channels, name=waited_game_result_channel_name)
                game_document = extract_game_document_from_db(f'Game {game_num}')
                game_players = game_document['player_list']

                result_img = await image_uploaded.to_file()
                gameResult = discord.Embed(title=f'Game {game_num} result', description=f'Image uploaded by {message.author.name}#{message.author.discriminator}')
                gameResult.add_field(name="Players", value=', '.join(game_players), inline=False) 
                gameResult.set_image(url=f"attachment://{result_img.filename}")
                await waited_game_result_channel.send(embed=gameResult, file=result_img)
                
                unchecked_game_result_channel_name = f'unchecked丨game-{game_num}-result' 
                await waited_game_result_channel.edit(name=unchecked_game_result_channel_name)
                
                await message.channel.send('Thank you. Result image has been sent, waiting for double check. Once done, this channel will be removed')
                
                unchecked_game_result_channel = discord.utils.get(guild.text_channels, name=unchecked_game_result_channel_name)
                await wait_for_double_check_and_update_db(client, unchecked_game_result_channel, game_document)

                await delay_delete_channel(10, message.channel)

                return
        

        


@client.event
async def on_voice_state_update(member, before, after):
    
    # Join to create
    personal_channel_name = f"{member.name}'s channel"
    personal_room_category_name = 'Personal hub'
    if str(after.channel) == 'Join to create':
        if str(after) != str(before):
            guild = member.guild            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            personal_category = await _get_category(guild, personal_room_category_name)
            personal_channel = await guild.create_voice_channel(name=personal_channel_name, overwrites=overwrites, category=personal_category)

            await member.move_to(personal_channel)
            
    # delete empty channel  
    if str(before.channel) == personal_channel_name:
        if str(after) != str(before):
            guild = member.guild
            personal_channel = discord.utils.get(guild.channels, name=personal_channel_name)
            await personal_channel.delete()


    # Waiting room, once the number of members is enough, move to team room, first come first served. 
    # Rememebr if you leave the waiting room in the meanwhile, you will need to wait again.
    team_waiting_room_name = 'Waiting room for team up'
    team_room_category_name = 'Team hub'
    if str(after.channel) == team_waiting_room_name:
        if str(after) != str(before):  
            guild = member.guild
            waiting_room = discord.utils.get(guild.channels, name=team_waiting_room_name)
            members = waiting_room.members #finds members connected to the channel
            sorted_member_index = get_sorted_member_index(members)
  
            number_of_members_to_go = 2
            if len(members) >= number_of_members_to_go:
                firstN_members = [members[i] for i in sorted_member_index]
                await create_team_channel_and_move_member(guild, firstN_members, team_room_category_name)
                
    # delete empty team channel 
    if str(before.channel).split()[0] == "Team":
        if str(after) != str(before):
            # delete sb's team role if sb leave
            team_role = discord.utils.get(member.guild.roles, name="{} role".format(str(before.channel)))
            # Todo: wait a tolerance time if member leave, but if he join again, then cancel the remove role  
            # maybe need a flag 
            # tolerance_time = 
            # await asyncio.sleep(tolerance_time)
            await member.remove_roles(team_role)    

            if len(before.channel.members) == 0:
                guild = member.guild
                team_room = discord.utils.get(guild.channels, name=str(before.channel))
                await team_room.delete()    
                
    game_waiting_room_name = 'Waiting room for gaming'
    game_room_category_name = 'Game hub'
    game_result_category_name = 'Game result'

    if str(after.channel) == game_waiting_room_name:
        if str(after) != str(before):  
            guild = member.guild
            waiting_room = discord.utils.get(guild.channels, name=game_waiting_room_name)
            members = waiting_room.members 
            sorted_member_index = get_sorted_member_index(members)
  
            number_of_members_to_go = 2
            if len(members) >= number_of_members_to_go:
                firstN_members = [members[i] for i in sorted_member_index]
                await create_game_channel_and_move_member(guild, firstN_members, game_room_category_name, game_result_category_name)
                
    # delete empty game channel 
    if str(before.channel).split()[0] == "Game":
        if str(after) != str(before):
            game_role = discord.utils.get(member.guild.roles, name="{} role".format(str(before.channel)))
            await member.remove_roles(game_role)    

            if len(before.channel.members) == 0:
                guild = member.guild
                game_room = discord.utils.get(guild.channels, name=str(before.channel))
                await game_room.delete()    


client.run(TOKEN)