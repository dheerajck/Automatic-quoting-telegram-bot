from pyrogram import Client, filters
from db.models import AdminChannel, BrokerChannel

from shared_config import shared_object


SUPER_ADMIN = shared_object.clients["super_admin"]

"""
ADMIN CHANNEL
"""


@Client.on_message(filters.user(SUPER_ADMIN) & filters.group & filters.command("add_admin", prefixes="!"))
async def add_admin_handler(client, message):
    await AdminChannel.objects.acreate(group_id=message.chat.id, title=message.chat.title)


@Client.on_message(filters.user(SUPER_ADMIN) & filters.group & filters.command("remove_admin", prefixes="!"))
async def remove_admin_handler(client, message):
    await AdminChannel.objects.filter(group_id=message.chat.id).adelete()


@Client.on_message(filters.user(SUPER_ADMIN) & filters.group & filters.command("list_admin", prefixes="!"))
async def list_admin_handler(client, message):
    output = ""
    async for channel in AdminChannel.objects.all():
        output += f"{channel.title } `{channel.group_id}`\n"
    await message.reply(output, quote=False)


"""
BROKER CHANNEL
"""


@Client.on_message(filters.user(SUPER_ADMIN) & filters.group & filters.command("add_broker", prefixes="!"))
async def add_broker_handler(client, message):
    await BrokerChannel.objects.acreate(group_id=message.chat.id, title=message.chat.title)


@Client.on_message(filters.user(SUPER_ADMIN) & filters.group & filters.command("remove_broker", prefixes="!"))
async def remove_broker_handler(client, message):
    await BrokerChannel.objects.filter(group_id=message.chat.id).adelete()


@Client.on_message(filters.user(SUPER_ADMIN) & filters.group & filters.command("list_broker", prefixes="!"))
async def list_broker_handler(client, message):
    output = ""
    async for channel in BrokerChannel.objects.all():
        output += f"{channel.title } `{channel.group_id}`\n"
    await message.reply(output, quote=False)