import os

from discord import Bot

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
if load_dotenv:
    load_dotenv(encoding='utf-8')

bot = Bot()


@bot.listen()
async def on_ready():
    print('bot: ready')


bot.load_extension('cogs.wod')
bot.run(os.getenv('DISCORD_KEY'))
