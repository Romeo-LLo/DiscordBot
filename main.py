from ntpath import join
from unicodedata import category
import discord
import os
from dotenv import load_dotenv

load_dotenv('---.env')

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
    
    if str(after.channel) == 'join to create':
        if str(after) != str(before):
            guild = member.guild            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            get_category = discord.utils.get(guild.categories, id=994513375247745075)  # get category first
            personal_channel = await guild.create_voice_channel(name=personal_channel_name, overwrites=overwrites, category=get_category)

            await member.move_to(personal_channel)
            
    if str(before.channel) == personal_channel_name:
        if str(after) != str(before):
            guild = member.guild
            personal_channel = discord.utils.get(guild.channels, name=personal_channel_name)
            await personal_channel.delete()


    # Waiting room, once the number of members is enough, move to game room, first come first served. 
    # Rememebr if you leave in the meanwhile, you will need to wait again.
    game_room_name = 'Ready game room'
    
    if str(after.channel) == 'Waiting room':
        if str(after) != str(before):  
            guild = member.guild
            waiting_room = discord.utils.get(guild.channels, name='Waiting room')
            members = waiting_room.members #finds members connected to the channel
            joined_time = [member.joined_at for member in members]
            sorted_index = sorted(range(len(members)), key=lambda k: joined_time[k])

            number_of_members_to_go = 2
            if len(members) >= number_of_members_to_go:
                firstN_members = [members[i] for i in sorted_index]
                firstN_role = await guild.create_role(name='firstN_members_role')

                overwrites = {
                    # guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.default_role: discord.PermissionOverwrite(connect=False),
                    firstN_role: discord.PermissionOverwrite(read_messages=True, send_messages= True)
                }
                
                get_category = discord.utils.get(guild.categories, id=994513375247745075)  # get category first
                game_room = await guild.create_voice_channel(name=game_room_name, overwrites=overwrites, category=get_category, user_limit=number_of_members_to_go)
                for member in firstN_members:
                    await member.add_roles(firstN_role)
                    await member.move_to(game_room)
                
    if str(before.channel) == game_room_name:
        if str(after) != str(before):
            if len(before.channel.members) == 0:
                guild = member.guild
                game_room = discord.utils.get(guild.channels, name=game_room_name)
                await game_room.delete()    



        




client.run("OTk0NTE0MTMwMzM5OTA1NTQ2.GtiJFd.J-cwN9RK0ujfyBLldnCye6ekAJt9DhW0_pIabs")