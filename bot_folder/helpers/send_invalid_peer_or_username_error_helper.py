async def send_invalid_peer_or_username_error_method(client, message, chat):
    try:
        int(chat)
    except ValueError:
        await message.reply("Invalid username")
    else:
        await message.reply("This bot hasnt seen this user or group yet, so cant resolve by id")
