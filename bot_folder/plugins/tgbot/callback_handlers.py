from pyrogram import Client, filters
from db.models import AdminChannel, BrokerChannel
from bot_folder.helpers import add_keyboad_button_and_send_text_message


@Client.on_callback_query(filters.regex("submit"))
async def user_submit(client, callback_query):
    """
    https://docs.pyrogram.org/api/types/CallbackQuery#pyrogram.types.CallbackQuery
    callback_query.from_user.username
    callback_query.message
    callback_query.data
    """
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text, reply_markup=None)

    # print(callback_query.message)

    await client.send_message(callback_query.message.chat.id, "done")

    # send it to admins
    async for group_id in AdminChannel.objects.all():
        await add_keyboad_button_and_send_text_message(
            client, group_id, callback_query.message.textext, "keyboard_button", "callback_data"
        )


@Client.on_callback_query(filters.regex("callback_data"))
async def admin_choice(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text, reply_markup=None)
    await client.send_message(callback_query.message.chat.id, "done")

    new_data = callback_query.message.text.split("\n")[4:]
    new_data = "\n".join(new_data).strip()

    async for group_id in BrokerChannel.objects.all():
        await add_keyboad_button_and_send_text_message(client, group_id, new_data, "keyboard_button", "callback_data")
