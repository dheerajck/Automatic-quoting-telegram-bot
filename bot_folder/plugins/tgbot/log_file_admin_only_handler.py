from pyrogram import Client, filters
from shared_config import shared_object


SUPER_ADMIN = shared_object.clients["super_admin"]


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("logfile", prefixes="!"))
async def logfile(client, message):
    """
    Returns the logfile
    """
    try:
        await message.reply_document(document="logfile.log", quote=True)
    except ValueError as error:
        await message.reply(error, quote=True)

    message.stop_propagation()
