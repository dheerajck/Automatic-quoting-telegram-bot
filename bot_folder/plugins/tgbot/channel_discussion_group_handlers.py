import asyncio

from pyrogram import Client, filters
from db.models import BrokerChannel, BotAdmins


async def get_top_message_object(client, message):
    """
    Returns the message object of the top message that the given message parameter has replied to.
    If the given message is not a reply, returns None.
    """

    if message.reply_to_top_message_id:
        # top message exist
        top_message = await client.get_messages(message.chat.id, message.reply_to_top_message_id)
    elif message.reply_to_message:
        # this message is a reply to a mesage but top message doesnt exist
        # top message exist directly imply that a message is a reply aswell
        top_message = message.reply_to_message
    else:
        top_message = None

    return top_message


async def is_admin(message):
    if message.from_user:
        return await BotAdmins.objects.filter(user_id=message.from_user.id).aexists()
    if message.sender_chat:
        # a user can send message as a group or channel, this can be an edge case in admin commands
        return False


@Client.on_message(filters.group & filters.reply & filters.command("close", prefixes="!"))
async def close_discussion_by_announcement_message(client, message):
    if await is_admin(message) is False:
        # this message is not from an admin
        return None

    top_message = await get_top_message_object(client, message)
    if top_message.forward_from_chat is None:
        # top of discussion is not forwarded from a channel
        return None

    is_forwarded_from_broker_channel = await BrokerChannel.objects.filter(
        group_id=top_message.forward_from_chat.id
    ).aexists()

    if is_forwarded_from_broker_channel is False:
        return None

    # remove admin command text from message text
    message_text = message.text.replace("!close", "", 1).strip()
    await message.delete()

    if message_text == "":
        temp_message = await top_message.reply("You need to specify final price per TH")
        await asyncio.sleep(2)
        await temp_message.delete()
    else:
        await top_message.reply(f"This deal has closed for a final price of {message_text} per TH")
