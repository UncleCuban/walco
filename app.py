import os
import re
import sqlite3
import discord
from embed import welcome_embed
from dotenv import find_dotenv, load_dotenv
from discord import app_commands
from discord.ext import commands
from file_access import append_to_file, find_user_on_file, update_user_wallet, get_user_ids, get_current_wallets
load_dotenv(find_dotenv())
sei_wallet_regex = r'^sei1[a-zA-Z0-9]{38}$'
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# DATABASE
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        file_id TEXT,
        sheet_name TEXT,
        monitoring_role_id INTEGER
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# ON READY
@bot.event
async def on_ready():
    print(f'Bot ready. Loged in as {bot.user.name}')
    try: 
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)

# COMMANDS
@bot.tree.command(name='info', description='Get all the information you need about your wallet collection bot')
@discord.app_commands.checks.has_permissions(administrator=True)
async def info(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(embed=welcome_embed())

@bot.tree.command(name='setup', description='Set the specifics variables of your collector bot')
@discord.app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    file='Google Sheets File ID, on the file URL, the ID is the string after `"https://docs.google.com/spreadsheets/d/"` and before the next `"/"`',
    sheet='Name of the sheet where you want the data to be stored',
    special_role='If you have an OG role and want to log who has it, select "True"',
    role='(optional) Specify the role to be logged if special_role is enabled'
)
async def setup(interaction: discord.Interaction, file: str, sheet: str, special_role: bool, role: discord.Role = None):
    await interaction.response.defer(ephemeral=True)
    try:
        with sqlite3.connect('bot_database.db') as conn:
            cur = conn.cursor()
            cur.execute(
                'REPLACE INTO guild_settings (guild_id, file_id, sheet_name, monitoring_role_id) VALUES (?, ?, ?, ?)',
                (interaction.guild.id, file, sheet, role.id if role and special_role else None)
            )
            conn.commit()

        message = 'Setup completed successfully'
        if special_role:
            message += ' with role logging enabled'
            if role:
                message += f'. Monitoring role: `{role.name}`'
            else:
                message += ' but no role has been specified. Please use the `/setup` command again to set the role.'
        else:
            message += ' with role logging disabled.'
        await interaction.followup.send(message)
    except Exception as e:
        await interaction.followup.send(f'Failed to store settings in the database. Please try again. Error: {str(e)}')

@bot.tree.command(name='wallet-collector', description='Submit your SEI wallet to be collected')
@app_commands.describe(wallet='SEI Wallet Address')
async def wallet_collector(interaction: discord.Interaction, wallet: str):
    await interaction.response.defer(ephemeral=True)
    with sqlite3.connect('bot_database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT file_id, sheet_name, monitoring_role_id FROM guild_settings WHERE guild_id = ?', (interaction.guild.id,))
        settings = cur.fetchone()

    if not settings:
        await interaction.followup.send('Please set up your guild settings first using the `/setup` command.')
    file_id, sheet_name, monitoring_role_id = settings
    monitored_role = discord.utils.find(lambda r: r.id == monitoring_role_id, interaction.guild.roles) if monitoring_role_id else None

    user_roles = interaction.user.roles
    has_monitored_role = monitored_role in user_roles if monitored_role else False
    role_info = monitored_role.name if has_monitored_role else ""
    user_name = interaction.user.display_name
    user_id = str(interaction.user.id)
    wallet_match = re.match(sei_wallet_regex, wallet)

    if wallet_match:
        users_who_submitted_wallets = get_user_ids(file_id, sheet_name)
        if user_id in users_who_submitted_wallets:
            message = 'You have already submitted your wallet, use command `/wallet-checker` to see if you sent the right one'
        else:
            current_wallets = get_current_wallets(file_id, sheet_name)     
            if wallet in current_wallets:
                message = 'This wallet is already registered'
            else:
                if append_to_file(file_id, sheet_name, user_name, wallet, user_id, role_info):
                    message = f'**Thank you for submitting your wallet, {interaction.user.display_name}!**\nCollected Wallet: `{wallet}`'
                    users_who_submitted_wallets.add(user_id)
                else:
                    message = 'There was an error collecting your wallet. Please contact a Staff member.'
    else:
        message = 'The provided address is not a valid SEI wallet address. Please check and try again.'
    await interaction.followup.send(message)

@bot.tree.command(name='wallet-checker', description='Check which wallet you have submitted')
async def wallet_checker(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    with sqlite3.connect('bot_database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT file_id, sheet_name FROM guild_settings WHERE guild_id = ?', (interaction.guild.id,))
        settings = cur.fetchone()

    if not settings:
        await interaction.followup.send('Please set up your guild settings first using the `/setup` command.')
    file_id, sheet_name = settings
    user_id = str(interaction.user.id)
    users_who_submitted_wallets = get_user_ids(file_id, sheet_name)
    if user_id in users_who_submitted_wallets:
        row_data = find_user_on_file(file_id, sheet_name, user_id)
        message = f'Submitted wallet: `{row_data[1]}`'
    else:
        message = f'You havent submitted your wallet yet, {interaction.user.display_name}. Please do so by using the command `/wallet-collector`'
    await interaction.followup.send(message)

@bot.tree.command(name='wallet-editor', description='Submit the propper SEI wallet that you want to be collected')
@app_commands.describe(new_wallet='Your propper SEI Wallet Address')
async def wallet_collector(interaction: discord.Interaction, new_wallet: str):
    await interaction.response.defer(ephemeral=True)
    with sqlite3.connect('bot_database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT file_id, sheet_name FROM guild_settings WHERE guild_id = ?', (interaction.guild.id,))
        settings = cur.fetchone()

    if not settings:
        await interaction.followup.send('Please set up your guild settings first using the `/setup` command.')
    file_id, sheet_name = settings
    match = re.match(sei_wallet_regex, new_wallet)
    if match:
        user_id = str(interaction.user.id)
        if update_user_wallet(file_id, sheet_name, user_id, new_wallet):
            message = f'**Your wallet is updated, {interaction.user.display_name}!**\nNew Wallet Collected: `{new_wallet}`'
        else:
            message = 'There was an error updating your wallet. Please contact a Core Team member.'
    else:
        message = 'The provided address is not a valid SEI wallet address. Please check and try again.'
    await interaction.followup.send(message)

bot.run(BOT_TOKEN)