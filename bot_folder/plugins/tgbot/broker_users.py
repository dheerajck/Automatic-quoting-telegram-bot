from django.db import IntegrityError
from pyrogram import Client, filters
from db.models import BrokerChannel
from pyrogram import enums

from shared_config import shared_object


async def get_user_details(client, message):
    try:
        user = message.command[1] if len(message.command) == 2 else ""
        user_object = await client.get_users(user)
    except Exception as e:
        # If bot cant find user from the information provided <username or user ID>,
        # send a clear error message why bot cant find the user
        await message.reply(e)
        return None
    else:
        return user_object


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("adduser", prefixes="!"))
async def add_broker_user_handler(client, message):
    if len(message.command) != 2:
        await message.reply("Specify user")
        message.stop_propagation()

    try:
        user = message.command[1]
        user_object = await client.get_chat(user)
    except Exception as e:
        await message.reply(e)
        message.stop_propagation()

    if user_object.type == enums.ChatType.PRIVATE:
        try:
            user_id = user_object.id
            full_name = user_object.first_name + (user_object.last_name or "")
            await BrokerChannel.objects.acreate(group_id=user_id, title=full_name, is_user=True)
            await message.reply(f"Added user {full_name} to broker groups")
        except IntegrityError:
            await message.reply(f"Added user {full_name} to broker groups")

    else:
        await message.reply("Specify user not group / channel")
    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("removeuser", prefixes="!"))
async def remove_broker_user_handler(client, message):
    user = message.command[1]
    try:
        user_object = await client.get_chat(user)
    except Exception as e:
        await message.reply(e)
        message.stop_propagation()

    if user_object.type == enums.ChatType.PRIVATE:
        full_name = user_object.first_name + (user_object.last_name or "")
        await BrokerChannel.objects.filter(group_id=user_object.id).adelete()
        await message.reply(f"Removed {full_name} from broker groups if he was a broker user")
    else:
        await message.reply("Specify user not group / channel")
    message.stop_propagation()


@Client.on_message(shared_object.clients["bot_admins"] & filters.command("listuser", prefixes="!"))
async def list_broker_user_handler(client, message):
    output = ""
    async for channel in BrokerChannel.objects.filter(is_user=True):
        output += f"{channel.title } `{channel.group_id}`\n"
    if output != "":
        await message.reply(output, quote=False)
    else:
        await message.reply("No Broker users are present in db", quote=False)
    message.stop_propagation()
