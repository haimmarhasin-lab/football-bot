import os
import asyncio
import logging
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
API_KEY = os.getenv("APIFOOTBALL_KEY")
STAKE = float(os.getenv("STAKE_EUR", 7))

ADMIN_IDS = list(
    map(int, os.getenv("ADMIN_IDS", "").split(","))
) if os.getenv("ADMIN_IDS") else []

API_BASE = "https://v3.football.api-sports.io"

FILE = "Football_Model_Rules_and_Diary.xlsx"


async def api_get(endpoint, params=None):
    headers = {"x-apisports-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}{endpoint}",
            headers=headers,
            params=params
        ) as r:
            return await r.json()


def init_diary():
    if os.path.exists(FILE):
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "Diary"
    ws.append(["Date", "Match", "Market", "Odds", "Stake"])
    wb.save(FILE)


def add_diary(match, market, odds):
    wb = load_workbook(FILE)
    ws = wb.active
    ws.append([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        match,
        market,
        odds,
        STAKE
    ])
    wb.save(FILE)


bot = Bot(BOT_TOKEN)
dp = Dispatcher()



@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("✅ Бот жив и отвечает")

async def prematch_scanner():
    while True:
        data = await api_get("/fixtures", {"live": "true"})
        for f in data.get("response", []):
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            text = f"🔴 LIVE\n{home} — {away}"
            await bot.send_message(CHANNEL_ID, text)
            add_diary(f"{home}-{away}", "LIVE CHECK", 1.85)
            break
        await asyncio.sleep(120)


async def main():
    init_diary()
    asyncio.create_task(prematch_scanner())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
