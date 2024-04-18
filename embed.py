import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

def welcome_embed():
    embed = discord.Embed(
        title='Welcome bot-master!',
        description='**This is __WALCO__, your Wallet Collection Bot**\nThis bot will help you collect wallet addresses easily and smoothly\n',
        color=discord.Color.dark_grey()
    )
    embed.add_field(
        name='Instructions',
        value='To start using the bot you need to follow these steps: \n**1.** Create a google sheets file and share it with the bot\'s email giving it \'Editor\' permissions.\n> Bot\'s Email: `client@walco-420518.iam.gserviceaccount.com`\n**2.** Run the `/setup` command and follow the instructions\n**3.** Ensure that all the values in the setup are correct.\n\n*Now your users can start interacting with the wallet collector*\nAs a precaution, ensure to modify the Bot\'s integration settings to allow access to the commands only on the desired channels and to the desired roles\n> `Server Settings > Integrations > WALCO`\n',
        inline=False
    )
    embed.add_field(
        name='Commands',
        value='`/setup` **(admin only)** - Set the specific variables of your collector bot\n`/wallet-collector` - Submit your SEI wallet to be collected\n`/wallet-checker` - Check the wallet you submitted\n`/wallet-editor` - Edit the wallet you submitted',
        inline=False
    )
    embed.add_field(
        name='Need help?',
        value='For any questions or claims, please contact the bot developer: [@UncleCuban](<https://x.com/unclecuban>)',
        inline=False
    )
    embed.set_image('/resources/avatar/WALCO_banner.png')
    embed.set_footer(
        text='WALCO - Wallet Collection Bot... Enjoy!'
    )
    return embed


