from django.db import IntegrityError
from pyrogram import Client, filters
from db.models import AdminChannel, BrokerChannel
from pyrogram import enums

from shared_config import shared_object

from bot_folder.helpers import send_invalid_peer_or_username_error_method


"""
ADMIN CHANNEL
"""


@Client.on_message(
    filters.user(shared_object.clients["bot_admins"]) & filters.command("add_admin_channel", prefixes="!")
)
async def add_admin_handler(client, message):
    if len(message.command) == 1:
        chat_object = message.chat
    else:
        chat = message.command[1]
        try:
            chat_object = await client.get_chat(chat)
        except Exception as e:
            await send_invalid_peer_or_username_error_method(client, message, chat)
            message.stop_propagation()

    if chat_object.type != enums.ChatType.PRIVATE:
        try:
            await AdminChannel.objects.acreate(group_id=chat_object.id, title=chat_object.title)
            await message.reply(f"Added {chat_object.title} to admin groups")
        except IntegrityError:
            await message.reply(f"Added {chat_object.title} to admin groups")

    else:
        await message.reply("You cant add users to Admin channel")
    message.stop_propagation()


@Client.on_message(
    filters.user(shared_object.clients["bot_admins"]) & filters.command("remove_admin_channel", prefixes="!")
)
async def remove_admin_handler(client, message):
    if len(message.command) == 1:
        chat_object = message.chat
    else:
        chat = message.command[1]
        try:
            chat_object = await client.get_chat(chat)
        except Exception as e:
            await send_invalid_peer_or_username_error_method(client, message, chat)
            message.stop_propagation()

    await AdminChannel.objects.filter(group_id=chat_object.id).adelete()
    await message.reply(f"Removed {message.chat.title} from admin groups")
    message.stop_propagation()


@Client.on_message(
    filters.user(shared_object.clients["bot_admins"]) & filters.command("list_admin_channel", prefixes="!")
)
async def list_admin_handler(client, message):
    output = ""
    async for channel in AdminChannel.objects.all():
        output += f"{channel.title} `{channel.group_id}`\n"
    if output != "":
        await message.reply(output, quote=False)
    else:
        await message.reply("No Admin channels present in db", quote=False)
    message.stop_propagation()


"""
BROKER CHANNEL
"""


@Client.on_message(
    filters.user(shared_object.clients["bot_admins"]) & filters.command("add_broker_channel", prefixes="!")
)
async def add_broker_handler(client, message):
    if len(message.command) == 1:
        chat_object = message.chat
    else:
        chat = message.command[1]
        try:
            chat_object = await client.get_chat(chat)
        except Exception as e:
            await send_invalid_peer_or_username_error_method(client, message, chat)
            message.stop_propagation()

    if chat_object.type != enums.ChatType.PRIVATE:
        try:
            await BrokerChannel.objects.acreate(group_id=chat_object.id, title=chat_object.title)
            await message.reply(f"Added {chat_object.title} to broker groups")
        except IntegrityError:
            await message.reply(f"Added {chat_object.title} to broker groups")

    else:
        await message.reply("You cant add users to Broker channel")
    message.stop_propagation()


@Client.on_message(
    filters.user(shared_object.clients["bot_admins"]) & filters.command("remove_broker_channel", prefixes="!")
)
async def remove_broker_handler(client, message):
    if len(message.command) == 1:
        chat_object = message.chat
    else:
        chat = message.command[1]
        try:
            chat_object = await client.get_chat(chat)
        except Exception as e:
            await send_invalid_peer_or_username_error_method(client, message, chat)
            message.stop_propagation()
    await BrokerChannel.objects.filter(group_id=chat_object.id).adelete()
    await message.reply(f"Removed {message.chat.title} to broker groups")
    message.stop_propagation()


@Client.on_message(
    filters.user(shared_object.clients["bot_admins"]) & filters.command("list_broker_channel", prefixes="!")
)
async def list_broker_handler(client, message):
    output = ""
    async for channel in BrokerChannel.objects.all():
        output += f"{channel.title } `{channel.group_id}`\n"
    if output != "":
        await message.reply(output, quote=False)
    else:
        await message.reply("No Broker channels present in db", quote=False)
    message.stop_propagation()
