import asyncio
from aiogram import Bot

TOKEN = "8311317527:AAEqp7DYz_r5e5azS511XXIteye-ovQKaAg"

async def check():
    bot = Bot(token=TOKEN)
    try:
        me = await bot.get_me()
        print(f"✅ TOKEN OK! Bot: @{me.username} | Name: {me.first_name}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check())
