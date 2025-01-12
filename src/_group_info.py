
import time
import asyncio
import sys
from pyrogram import Client
import pandas as pd
import json

# See: https://core.telegram.org/api/obtaining_api_id
api_id = 1
api_hash = "..."

app = Client("me", api_id, api_hash)

async def main():
    async with app:
        async for dialog in app.get_dialogs():
            if "sosbird_chto_tut_bot_test_group" in str(dialog):
                print(dialog)

app.run(main())
