import discord
from discord.ext import commands
from discord.interactions import Interaction
import os

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
intents = discord.Intents.default()

TOKEN = os.environ.get("TOKEN")


@bot.event
async def on_ready():
    print("Bot is UP and Ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.tree.command(name='ping', description='latency check command')
async def ping(interaction: discord.Interaction):
    bot_latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Latency: {bot_latency}ms')


@bot.tree.command(name='say', description='say command')
async def say(interaction: discord.Interaction, *, message: str):
    await interaction.response.send_message(message)

# admin only command to create channels


@bot.tree.command(name='create', description='create channel command')
@commands.has_permissions(administrator=True)
async def create(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Creating channel: {name}')
    await interaction.guild.create_text_channel(name)

# admin only command to delete channels


@bot.tree.command(name='delete', description='delete channel command')
@commands.has_permissions(administrator=True)
async def delete(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Deleting channel: {name}')
    channel = discord.utils.get(interaction.guild.channels, name=name)
    await channel.delete()

# admin only command to create roles


@bot.tree.command(name='createrole', description='create role command')
@commands.has_permissions(administrator=True)
async def createrole(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Creating role: {name}')
    await interaction.guild.create_role(name=name)

# admin only command to delete roles


@bot.tree.command(name='deleterole', description='delete role command')
@commands.has_permissions(administrator=True)
async def deleterole(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Deleting role: {name}')
    role = discord.utils.get(interaction.guild.roles, name=name)
    await role.delete()


bot.run(TOKEN)
