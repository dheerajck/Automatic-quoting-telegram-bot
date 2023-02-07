import logging

from pyrogram import Client, filters
from pyrogram.errors import BadRequest, Forbidden

from db.models import AdminChannel, BrokerChannel
from bot_folder.helpers import add_keyboad_button_and_send_text_message


@Client.on_callback_query(filters.regex("SUBMIT"))
async def user_submit(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text.html, reply_markup=None)

    response = "Thank you for your request, we have begun sourcing the best offers across the verified brokers network, and will get back to you as soon as possible."
    await client.send_message(callback_query.message.chat.id, response)

    # send it to admins

    async for group in AdminChannel.objects.all():
        try:
            forwarded_message = await callback_query.message.forward(group.group_id)
            await add_keyboad_button_and_send_text_message(
                client,
                group.group_id,
                "Do you want to send above text to broker channels ??",
                "SEND TO BROKER CHANNELS",
                f"SEND {group.group_id} {forwarded_message.id}",
            )
        except (BadRequest, Forbidden) as e:
            logging.exception(e)


@Client.on_callback_query(filters.regex(r"SEND -?\d+(\d+)? -?\d+(\d+)?"))
async def admin_choice(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text, reply_markup=None)

    data = callback_query.data
    _, group_id, message_id = data.split()
    # ERROR:pyrogram.dispatcher:'str' object has no attribute 'to_bytes'
    # print(group_id, message_id)
    group_id = int(group_id)
    message_id = int(message_id)

    new_message = await client.get_messages(group_id, message_id)
    # new_data = new_message.text.split("\n")[6:]
    new_data = new_message.text[new_message.text.index("Quantity") :]
    # new_data = "\n".join(new_data).strip()

    async for group in BrokerChannel.objects.all():
        try:
            temp_message = await client.send_message(group.group_id, new_data)
            response = f"Quote sent to broker channel ([link of message in broker channel]({temp_message.link}))"
            # print(temp_message)
            await client.send_message(callback_query.message.chat.id, response)
        except BadRequest as e:
            logging.exception(e)
