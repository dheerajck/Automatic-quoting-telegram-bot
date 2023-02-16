import asyncio
import os

import uvloop
from dotenv import load_dotenv

from pyrogram import Client, compose

from simple_logging.standard_logging_loguru_interface_class import set_logger

from shared_config import shared_object
from db.models import BotAdmins

# load env
load_dotenv("bot_folder/.env")

# set logging
set_logger()

# set uvloop
uvloop.install()


async def main():
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    bot_token = os.getenv('BOT_TOKEN')
    shared_object.clients["super_admin"] = os.getenv('SUPER_ADMIN')

    plugins_tgbot = dict(
        root="bot_folder.plugins.tgbot/",
    )

    bot = Client("tgbot", api_id=api_id, api_hash=api_hash, bot_token=bot_token, plugins=plugins_tgbot)

    shared_object.clients["tgbot"] = bot

    shared_object.clients["bot_admins"] = [
        user_id async for user_id in BotAdmins.objects.all().values_list("user_id", flat=True)
    ]

    async with bot:
        bot_details = await bot.get_me()
        await bot.send_message(
            shared_object.clients["super_admin"],
            f"@{bot_details.username} started",
        )

        admin_object = await bot.get_users(
            shared_object.clients["super_admin"],
        )

    shared_object.clients["super_admin"] = admin_object.id
    shared_object.clients["bot_admins"].append(admin_object.id)

    apps = [bot]
    await compose(apps)


def uvloop_test():
    loop = asyncio.new_event_loop()
    print(isinstance(loop, uvloop.Loop))
    assert isinstance(loop, uvloop.Loop)


if __name__ == "__main__":
    asyncio.run(main())
