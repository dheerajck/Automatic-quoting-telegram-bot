from django.db import IntegrityError
from pyrogram import Client, filters
from pyrogram import enums

from db.models import AdminChannel, BrokerChannel


from shared_config import shared_object

from bot_folder.helpers import send_invalid_peer_or_username_error_method


"""
ADMIN CHANNEL
"""


async def get_chat_details(client, message):
    try:
        chat = message.command[1] if len(message.command) == 2 else ""
        chat_object = await client.get_users(chat)
    except Exception:
        # If bot cant find user from the information provided <chat username or chat ID>,
        # send a clear error message why bot cant find the chat
        await send_invalid_peer_or_username_error_method(client, message, chat)
        return None
    else:
        if chat_object.type == enums.ChatType.PRIVATE:
            await message.reply("You cant add users to Admin channel")
            return None
        else:
            return chat_object


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("addadminchannel", prefixes="!"))
async def add_admin_handler(client, message):
    """
    This is a message handler to add a new admin channel.
    The user must be a bot admin in order use this command.
    The command syntax is: !add_admin_channel <chat username or chat ID>
    """

    chat_object = await get_chat_details(client, message)

    if chat_object:
        try:
            await AdminChannel.objects.acreate(group_id=chat_object.id, title=chat_object.title)
            await message.reply(f"Added {chat_object.title} to admin groups")
        except IntegrityError:
            await message.reply(f"{chat_object.title} already in admin groups")

    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("removeadminchannel", prefixes="!"))
async def remove_admin_handler(client, message):
    """
    This is a message handler to remove an admin channel.
    The user must be a bot admin in order use this command.
    The command syntax is: !remove_admin_channel <chat username or chat ID>
    """

    chat_object = await get_chat_details(client, message)

    if chat_object:
        await AdminChannel.objects.filter(group_id=chat_object.id).adelete()
        await message.reply(f"Removed {message.chat.title} from admin groups if they were in  admin groups")

    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("listadminchannel", prefixes="!"))
async def list_admin_handler(client, message):
    """
    This is a message handler to list all admin channels.
    The user must be a bot admin in order use this command.
    The command syntax is: !list_admin_channel
    """

    output = "List of admins channels\n"

    async for channel in AdminChannel.objects.all():
        output += f"{channel.title} `{channel.group_id}`\n"

    output = output if output != "List of admins\n" else "No admin channels present in the db"
    await message.reply(output, quote=False)

    message.stop_propagation()


"""
BROKER CHANNEL
"""


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("addbrokerchannel", prefixes="!"))
async def add_broker_handler(client, message):
    """
    This is a message handler to add a new broker channel.
    The user must be a bot admin in order use this command.
    The command syntax is: !add_broker_channel <chat username or chat ID>
    """

    chat_object = await get_chat_details(client, message)

    if chat_object:
        try:
            await BrokerChannel.objects.acreate(group_id=chat_object.id, title=chat_object.title)
            await message.reply(f"Added {chat_object.title} to broker groups")
        except IntegrityError:
            await message.reply(f"{chat_object.title} already in broker groups")

    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("removebrokerchannel", prefixes="!"))
async def remove_broker_handler(client, message):
    """
    This is a message handler to remove an broker channel.
    The user must be a bot admin in order use this command.
    The command syntax is: !remove_broker_channel <chat username or chat ID>
    """

    chat_object = await get_chat_details(client, message)

    if chat_object:
        await BrokerChannel.objects.filter(group_id=chat_object.id).adelete()
        await message.reply(f"Removed {message.chat.title} from broker groups if they were in  broker groups")

    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("listbrokerchannel", prefixes="!"))
async def list_broker_handler(client, message):
    """
    This is a message handler to list all broker channels.
    The user must be a bot admin in order use this command.
    The command syntax is: !list_broker_channel
    """

    output = "List of broker channels\n"

    async for channel in AdminChannel.objects.all():
        output += f"{channel.title} `{channel.group_id}`\n"

    output = output if output != "List of admins\n" else "No broker channels present in the db"
    await message.reply(output, quote=False)

    message.stop_propagation()
