import discord
from discord import app_commands
from discord.ext import commands
from wg_easy_api_wrapper import Server
from wg_easy_api_wrapper.client import Client
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="wg!", intents=intents)

dotenv = load_dotenv()
token = os.getenv("TOKEN")
password = os.getenv("PASSWORD")
url = os.getenv("URL")

async def create(discord_id, name, common_name):
    async with Server(url, password) as server:
        conf_name = f"{name} • {discord_id} : {common_name}"
        clients = await server.get_clients()
        if any(client.name == conf_name for client in clients):
            return False, "Configuration already exists"
        else:
            await server.create_client(conf_name)
            clients = await server.get_clients()
            precise_conf = [client for client in clients if client.name == conf_name]
            retrieved_conf = await Client.get_configuration(precise_conf[0])
            with open(f"configs/{conf_name}.conf", "w") as file:
                file.write(retrieved_conf)
            return True, f"configs/{conf_name}.conf"


@bot.tree.command(name="generate", description="Génère une configuration wireguard")
@app_commands.describe(name="Le nom de ta config wireguard")
async def generate(interaction: discord.Interaction, name: str):
    discord_name = interaction.user.name
    discord_id = interaction.user.id
    common_name = name
    status, path = await create(discord_id, discord_name, common_name)
    if status:
        await interaction.response.send_message(f"Configuration générée pour {discord_name} : {common_name}", file=discord.File(path), ephemeral=True)
    else:
        await interaction.response.send_message(f"Erreur : La configuration existe déjà !", ephemeral=True)


@bot.tree.command(name="list", description="Liste tes configurations wireguard")
async def list(interaction: discord.Interaction):
    discord_id = interaction.user.id
    async with Server(url, password) as server:
        clients = await server.get_clients()
        user_clients = [client for client in clients if str(discord_id) in client.name]
        if user_clients:
            await interaction.response.send_message("__**Liste de tes configurations: **__\n\n"+ "\n".join([client.name for client in user_clients]), ephemeral=True)
        else:
            await interaction.response.send_message("Aucune configuration trouvée", ephemeral=True)


@bot.tree.command(name="get", description="Récupère une configuration wireguard")
@app_commands.describe(name="Le nom de ta config wireguard")
async def get(interaction: discord.Interaction, name: str):
    discord_id = interaction.user.id
    async with Server(url, password) as server:
        clients = await server.get_clients()
        user_clients = [client for client in clients if str(discord_id) in client.name]
        precise_conf = [client for client in user_clients if name in client.name]
        if precise_conf:
            retrieved_conf = await Client.get_configuration(precise_conf[0])
            with open(f"configs/{precise_conf[0].name}.conf", "w") as file:
                file.write(retrieved_conf)
            await interaction.response.send_message(f"Configuration récupérée pour {precise_conf[0].name}", file=discord.File(f"configs/{precise_conf[0].name}.conf"), ephemeral=True)
        else:
            await interaction.response.send_message("Configuration introuvable", ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="🐉 • The Wireguard Master"), status=discord.Status.online)

bot.run(token)