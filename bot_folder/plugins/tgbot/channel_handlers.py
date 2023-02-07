from django.db import IntegrityError
from pyrogram import Client, filters
from db.models import AdminChannel, BrokerChannel
from pyrogram import enums

from shared_config import shared_object

from bot_folder.helpers import send_invalid_peer_or_username_error_method


SUPER_ADMIN = shared_object.clients["super_admin"]

BOT_ADMIN = shared_object.clients["bot_admins"]

ADMINS = [SUPER_ADMIN] + BOT_ADMIN


"""
ADMIN CHANNEL
"""


@Client.on_message(filters.user(ADMINS) & filters.command("add_admin", prefixes="!"))
async def add_admin_handler(client, message):
    if len(message.command) == 1:
        chat_object = message.chat
    else:
        chat = message.command[1]
        try:
            chat_object = await client.get_chat(chat)
        except Exception as e:
            await send_invalid_peer_or_username_error_method(client, message, chat)
            message.stop_propogation()

    if chat_object.chat.type != enums.PRIVATE:
        try:
            await AdminChannel.objects.acreate(group_id=chat_object.id, title=message.chat_object.title)
            await message.reply(f"Added {message.chat.title} to admin groups")
        except IntegrityError:
            pass

    else:
        await message.reply("You cant add users to Admin channel")


@Client.on_message(filters.user(ADMINS) & filters.command("remove_admin", prefixes="!"))
async def remove_admin_handler(client, message):
    await AdminChannel.objects.filter(group_id=message.chat.id).adelete()
    await message.reply(f"Removed {message.chat.title} from admin groups")


@Client.on_message(filters.user(ADMINS) & filters.command("list_admin", prefixes="!"))
async def list_admin_handler(client, message):
    output = ""
    async for channel in AdminChannel.objects.all():
        output += f"{channel.title } `{channel.group_id}`\n"
    await message.reply(output, quote=False)


"""
BROKER CHANNEL
"""


@Client.on_message(filters.user(ADMINS) & filters.command("add_broker", prefixes="!"))
async def add_broker_handler(client, message):
    if len(message.command) == 1:
        chat_object = message.chat
    else:
        chat = message.command[1]
        try:
            chat_object = await client.get_chat(chat)
        except Exception as e:
            await send_invalid_peer_or_username_error_method(client, message, chat)
            message.stop_propogation()

    if chat_object.chat.type != enums.PRIVATE:
        try:
            await BrokerChannel.objects.acreate(group_id=message.chat.id, title=message.chat.title)
            await message.reply(f"Added {message.chat.title} to broker groups")
        except IntegrityError:
            pass

    else:
        await message.reply("You cant add users to Broker channel")


@Client.on_message(filters.user(ADMINS) & filters.command("remove_broker", prefixes="!"))
async def remove_broker_handler(client, message):
    await BrokerChannel.objects.filter(group_id=message.chat.id).adelete()
    await message.reply(f"Removed {message.chat.title} to broker groups")


@Client.on_message(filters.user(ADMINS) & filters.command("list_broker", prefixes="!"))
async def list_broker_handler(client, message):
    output = ""
    async for channel in BrokerChannel.objects.all():
        output += f"{channel.title } `{channel.group_id}`\n"
    await message.reply(output, quote=False)
