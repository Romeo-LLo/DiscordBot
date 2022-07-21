from ntpath import join
from pickle import FALSE
from unicodedata import category
import discord
import os
from dotenv import load_dotenv
from utils import _get_category, create_team_channel_and_move_member

# load_dotenv('---.env')
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
           

@client.event
async def on_voice_state_update(member, before, after):
    
    # Join to create
    personal_channel_name = f"{member.name}'s channel"
    
    if str(after.channel) == 'Join to create':
        if str(after) != str(before):
            guild = member.guild            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            personal_room_category_name = 'Personal room hub'

            personal_category = await _get_category(guild, personal_room_category_name)

            personal_channel = await guild.create_voice_channel(name=personal_channel_name, overwrites=overwrites, category=personal_category)

            await member.move_to(personal_channel)
            
    if str(before.channel) == personal_channel_name:
        if str(after) != str(before):
            guild = member.guild
            personal_channel = discord.utils.get(guild.channels, name=personal_channel_name)
            await personal_channel.delete()


    # Waiting room, once the number of members is enough, move to game room, first come first served. 
    # Rememebr if you leave in the meanwhile, you will need to wait again.
    game_room_name = 'Game room'
    
    if str(after.channel) == 'Waiting room':
        if str(after) != str(before):  
            guild = member.guild
            waiting_room = discord.utils.get(guild.channels, name='Waiting room')
            members = waiting_room.members #finds members connected to the channel
            joined_time = [member.joined_at for member in members]
            sorted_index = sorted(range(len(members)), key=lambda k: joined_time[k])
            
            game_room_category_name = 'Game room hub'
  
            number_of_members_to_go = 2
            if len(members) >= number_of_members_to_go:
                firstN_members = [members[i] for i in sorted_index]
                await create_team_channel_and_move_member(guild, firstN_members, game_room_category_name)

                
    if str(before.channel).split()[0] == "Team":
        if str(after) != str(before):
            if len(before.channel.members) == 0:
                guild = member.guild
                game_room = discord.utils.get(guild.channels, name=str(before.channel))
                await game_room.delete()    




client.run(TOKEN)