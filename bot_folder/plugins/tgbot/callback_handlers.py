import logging

import xxhash

from pyrogram import Client, filters
from pyrogram.errors import BadRequest, Forbidden

from db.models import AdminChannel, BrokerChannel

from db.models import (
    Conversations,
    ConversationIdentifier,
    ConversationBackups,
)

from bot_folder.helpers import add_keyboad_button_and_send_text_message


from datetime import datetime, timezone


@Client.on_callback_query(filters.regex("SUBMIT"))
async def user_submit(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text.html, reply_markup=None)

    final_message = callback_query.message.text.markdown.strip()

    # added_time = datetime.now(timezone.utc)
    added_time_str = final_message.split("\n")[0].replace("Date: ", "").strip()
    added_time = datetime.strptime(added_time_str, '%d %b %Y at %H:%M:%S %Z')

    user_id = callback_query.from_user.id

    quote_id = xxhash.xxh32(final_message.encode("utf-8"), seed=12718745).hexdigest()

    conversation_key = await ConversationIdentifier.objects.acreate(
        user_id=user_id, added=added_time, quote_id=quote_id
    )
    # await ConversationIdentifier.objects.filter(id=conversation_key.id).aupdate(quote_id=quote_id)

    QUERY = []

    async for conversation_data in Conversations.objects.filter(user_id=user_id).order_by("question_order"):
        QUERY.append(
            ConversationBackups(
                conversation_identifier=conversation_key,
                question_order=conversation_data.question_order,
                question=conversation_data.question,
                response=conversation_data.response,
                private_question=conversation_data.private_question,
            )
        )

    await ConversationBackups.objects.abulk_create(QUERY)
    await Conversations.objects.filter(user_id=user_id).adelete()

    response_to_user = (
        f"Thank you for your request, we have begun sourcing the best offers across the verified brokers network, and will get back to you as soon as possible.\n"
        "To start a new quote send /newquote again"
    )

    await client.send_message(callback_query.message.chat.id, response_to_user)

    # send it to admins
    interaction_question_with_quote_id = (
        f"Quote ID: {quote_id}\n" + "Do you want to send this quote to broker channels ??"
    )

    async for group in AdminChannel.objects.all():
        try:
            forwarded_message = await callback_query.message.forward(group.group_id)
            await add_keyboad_button_and_send_text_message(
                client,
                group.group_id,
                interaction_question_with_quote_id,
                {"SEND TO BROKER CHANNELS": "SEND"},
            )
        except (BadRequest, Forbidden) as e:
            logging.exception(e)


@Client.on_callback_query(filters.regex(r"SEND"))
async def admin_choice(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text, reply_markup=None)

    final_message = callback_query.message.text
    quote_id = final_message.split("\n")[0].replace("Quote ID: ", "").strip()

    question_answer = []

    conversation_identifier_object = await ConversationIdentifier.objects.filter(quote_id=quote_id).afirst()

    async for conversation_backup in ConversationBackups.objects.filter(
        conversation_identifier=conversation_identifier_object.id
    ).exclude(private_question=True):
        question_answer.append(f"{conversation_backup.question}\n{conversation_backup.response}\n")

    final_data = "\n".join(question_answer).strip()
    final_data = f"Quote ID: {quote_id}\n" + final_data

    async for group in BrokerChannel.objects.all():
        try:
            temp_message = await client.send_message(group.group_id, final_data)
            response = f"Quote sent to broker channel ([link of message in broker channel]({temp_message.link}))"
            # print(temp_message)
            await client.send_message(callback_query.message.chat.id, response)
        except BadRequest as e:
            logging.exception(e)


@Client.on_callback_query(filters.regex("CANCEL"))
async def user_cancel(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text.html, reply_markup=None)

    await Conversations.objects.filter(user_id=callback_query.from_user.id).adelete()

    response_to_user = "Your request has been cancelled\n" + "To start a new quote send /newquote again"
    await client.send_message(callback_query.message.chat.id, response_to_user)
