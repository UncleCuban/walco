import os
import re
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import find_dotenv, load_dotenv
from file_access import initialize_sheet, append_to_file, find_user_on_file, update_user_wallet, get_user_ids, get_current_wallets
from embed import welcome_embed

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
BOT_TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
sei_wallet_regex = r'^sei1[a-zA-Z0-9]{38}$'
users_who_submitted_wallets = set()
current_wallets = set()

@bot.event
async def on_ready():
    print(f'Bot ready. Loged in as {bot.user.name}')
    try: 
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)
#     users_who_submitted_wallets.update(get_user_ids())
#     current_wallets.update(get_current_wallets())

@bot.tree.command(name='info', description='Get all the information you need about your wallet collection bot')
@discord.app_commands.checks.has_permissions(administrator=True)
async def info(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(embed=welcome_embed())

# async def role_autocomplete(interaction: discord.Interaction, current: str):
#     return [discord.app_commands.Choice(name=role.name, value=role.id) for role in interaction.guild.roles if current.lower() in role.name.lower()]

# Commmand set the specifics of the wallet collection bot
@bot.tree.command(name='setup', description='Set the specifics variables of your collector bot')
@discord.app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    file='Google Sheets File ID',
    sheet='Name of the sheet where you want the data to be stored',
    log_roles='Do you want to record roles of the users who sumbit wallets?',
    roles='(optional) Specify the roles to be recorded'
)
# @app_commands.autocomplete(roles=role_autocomplete)
async def setup(interaction: discord.Interaction, file: str, sheet: str, log_roles: bool, roles: discord.Role = None):
    await interaction.response.defer(ephemeral=True)
    if log_roles and roles is None:
        await interaction.followup.send('You chose to log roles, but did not specify which roles to log. Please provide the roles.')
        return
    if initialize_sheet(file, sheet):
        message = f'Setup initialized successfully with role-logging {"enabled" if log_roles else "disabled"}.'
        if roles:
            message += f' Monitoring roles: {roles.name}'
    else:
        message = 'There was an error initializing the bot.'
    await interaction.followup.send(message)


# Commmand to submit wallet for collection
@bot.tree.command(name='wallet-collector', description='Submit your SEI wallet to be collected')
@app_commands.describe(wallet='SEI Wallet Address')
async def wallet_collector(interaction: discord.Interaction, wallet: str):
    await interaction.response.defer(ephemeral=True)
    # user data
    user_name = interaction.user.display_name
    user_id = str(interaction.user.id)
    # requirements
    wallet_match = re.match(sei_wallet_regex, wallet)

    if wallet_match:        
        if user_id in users_who_submitted_wallets:
            message = 'You have already submitted your wallet, use command `/wallet-checker` to see if you sent the right one'
        else:
            if len(users_who_submitted_wallets) <= 400: # Adjust for the desired cap on GTD mint spots
                if wallet in current_wallets:
                    message = 'This wallet is already registered'
                else:
                    if append_to_file(user_name, wallet, user_id):
                        message = f'**Thank you for submitting your wallet, {interaction.user.display_name}!**\nCollected Wallet: `{wallet}`'
                        users_who_submitted_wallets.add(user_id)
                    else:
                        message = 'There was an error collecting your wallet. Please contact a Core Team member.'
            else:
                message = 'All GTD mint spots have been filled, should\'ve been faster, lol.'
    else:
        message = 'The provided address is not a valid SEI wallet address. Please check and try again.'
    await interaction.followup.send(message)

@bot.tree.command(name='wallet-checker', description='Check which wallet you have submitted')
async def wallet_checker(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    if user_id in users_who_submitted_wallets:
        row_data = find_user_on_file(user_id)
        message = f'Submitted wallet: `{row_data[1]}`'
    # Processing in case the user has never submit their wallet
    else:
        message = f'You havent submitted your wallet yet, {interaction.user.display_name}. Please do so by using the command `/wallet-collector`'
    await interaction.followup.send(message)

# Commmand to edit the wallet on registry
@bot.tree.command(name='wallet-editor', description='Submit the propper SEI wallet that you want to be collected')
@app_commands.describe(new_wallet='Your propper SEI Wallet Address')
async def wallet_collector(interaction: discord.Interaction, new_wallet: str):
    await interaction.response.defer(ephemeral=True)
    match = re.match(sei_wallet_regex, new_wallet)
    if match:
        user_id = str(interaction.user.id)
        if update_user_wallet(user_id, new_wallet):
            message = f'**Your wallet is updated, {interaction.user.display_name}!**\nNew Wallet Collected: `{new_wallet}`'
        else:
            message = 'There was an error updating your wallet. Please contact a Core Team member.'
    else:
        message = 'The provided address is not a valid SEI wallet address. Please check and try again.'
    await interaction.followup.send(message)



bot.run(BOT_TOKEN)