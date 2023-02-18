from django.db import IntegrityError
from pyrogram import Client, filters
from db.models import BotAdmins

from shared_config import shared_object

from bot_folder.helpers import send_invalid_peer_or_username_error_method


async def get_user_details(client, message):
    try:
        user = message.command[1] if len(message.command) == 2 else ""
        user_object = await client.get_users(user)
    except Exception:
        # If bot cant find user from the information provided <username or user ID>,
        # send a clear error message why bot cant find the user
        await send_invalid_peer_or_username_error_method(client, message, user)
        return None
    else:
        return user_object


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("add_bot_admin", prefixes="!"))
async def add_bot_admin(client, message):
    """
    This is a message handler to add new bot admin.
    The user must be super admin in order use this command.
    The command syntax is: !add_bot_admin <username or user ID>
    """

    user_object = await get_user_details(client, message)

    if user_object:
        # If the <username or user ID> is valid, add that user as a bot admin
        name = user_object.first_name + (user_object.last_name or "")
        try:
            await BotAdmins.objects.acreate(user_id=user_object.id, name=name)
        except IntegrityError:
            await message.reply(f"{name} is already a bot admin")
        else:
            shared_object.clients["bot_admins"].add(user_object.id)
            await message.reply(f"Added {name} as bot admin")

    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("remove_bot_admin", prefixes="!"))
async def remove_bot_admin(client, message):
    """
    This is a message handler to remove a user from bot admin list.
    The user must be super admin in order use this command.
    The command syntax is: !remove_bot_admin <username or user ID>
    """

    user_object = await get_user_details(client, message)

    if user_object:
        name = user_object.first_name + (user_object.last_name or "")
        await BotAdmins.objects.filter(user_id=user_object.id).adelete()
        shared_object.clients["bot_admins"].discard(user_object.id)
        await message.reply(f"Removed {name} from bot admin if they were bot admin")

    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("list_bot_admin", prefixes="!"))
async def list_bot_admin(client, message):
    """
    This is a message handler to list all bot admins.
    The user must be super admin in order use this command.
    The command syntax is: !list_bot_admin
    """

    output = "List of admins\n"

    async for admin in BotAdmins.objects.all():
        output += f"{admin.name } `{admin.user_id}`\n"

    output = output if output != "List of admins\n" else "No bot admins in the db"
    await message.reply(output, quote=False)

    message.stop_propagation()
