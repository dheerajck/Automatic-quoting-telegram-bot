from django.db import IntegrityError
from pyrogram import Client, filters
from db.models import BotAdmins

from shared_config import shared_object


SUPER_ADMIN = shared_object.clients["super_admin"]


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("add_bot_admin", prefixes="!"))
async def add_bot_admin(client, message):
    message_text = message.text

    try:
        user = message_text.replace("!add_bot_admin", "", 1).strip()
        user_object = await client.get_users(user)
        if user_object.username == SUPER_ADMIN:
            message.stop_propagation()
            return None

    except Exception:
        try:
            int(user)
        except ValueError:
            await message.reply("Invalid username")
        else:
            await message.reply("This bot hasnt seem this user yet, so cant resolve by id")
        message.stop_propagation()

    else:
        name = user_object.first_name + (user_object.last_name or "")
        try:
            await BotAdmins.objects.acreate(user_id=user_object.id, name=name)
        except IntegrityError:
            pass

        shared_object.clients["bot_admins"] = [
            user_id async for user_id in BotAdmins.objects.all().values_list("user_id", flat=True)
        ]
        await message.reply(f"Added {name} as bot admin")
        message.stop_propagation()


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("remove_bot_admin", prefixes="!"))
async def remove_bot_admin(client, message):
    message_text = message.text
    try:
        user = message_text.replace("!remove_bot_admin", "", 1).strip()
        user_object = await client.get_users(user)
        if user_object.username == SUPER_ADMIN:
            message.stop_propagation()
            return None

    except Exception:
        try:
            int(user)
        except ValueError:
            await message.reply("Invalid username")
        else:
            await message.reply("This bot hasnt seem this user yet, so cant resolve by id")
        message.stop_propagation()
    else:
        name = user_object.first_name + (user_object.last_name or "")
        await BotAdmins.objects.filter(user_id=user_object.id).adelete()
        shared_object.clients["bot_admins"] = [
            user_id async for user_id in BotAdmins.objects.all().values_list("user_id", flat=True)
        ]
        await message.reply(f"Removed {name} from bot admin")
        message.stop_propagation()


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("list_bot_admin", prefixes="!"))
async def list_bot_admin(client, message):
    output = "List of admins\n"
    async for admin in BotAdmins.objects.all():
        output += f"{admin.name } `{admin.user_id}`\n"
    output = output if output != "List of admins\n" else "No bot admins in the list"
    await message.reply(output, quote=False)
    message.stop_propagation()
