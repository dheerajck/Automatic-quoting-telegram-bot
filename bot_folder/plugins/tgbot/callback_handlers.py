import logging
import asyncio

from datetime import datetime, timezone
import xxhash

from shared_config import shared_object


from pyrogram import Client, filters
from pyrogram.errors import BadRequest, Forbidden

from db.models import AdminChannel, BrokerChannel, Conversations

from db.models import (
    Conversations,
    ConversationIdentifier,
    ConversationBackups,
)

from bot_folder.helpers import add_keyboad_button_and_send_text_message


@Client.on_callback_query(filters.regex("SUBMIT"))
async def user_submit(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text.html, reply_markup=None)

    final_message = callback_query.message.text.markdown.strip()

    added_time_str = final_message.split("\n")[0].replace("Date: ", "").strip()
    added_time = datetime.strptime(added_time_str, '%d %b %Y at %H:%M:%S %Z')
    added_time = added_time.replace(tzinfo=timezone.utc)

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
        "Thank you for your request, we have begun sourcing the best offers across the verified brokers network, and will get back to you as soon as possible.\n"
        "To start a new quote send /newquote again"
    )

    await client.send_message(callback_query.message.chat.id, response_to_user)

    # send it to admins
    interaction_question_with_quote_id = (
        f"Quote ID: {quote_id}\n" + "Do you want to send this quote to broker channels ??"
    )

    async for group in AdminChannel.objects.all():
        try:
            await callback_query.message.forward(group.group_id)
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
    # await callback_query.answer(cache_time=100)
    # await callback_query.message.edit_text(callback_query.message.text, reply_markup=None)

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

    admin_broker_channel = await BrokerChannel.objects.filter(is_user=False).afirst()

    try:
        temp_message = await client.send_message(admin_broker_channel.group_id, final_data)

        response = f"Quote sent to broker channel ([link of message in broker channel]({temp_message.link}))"
        await client.send_message(callback_query.message.chat.id, response)

        async for broker_user in BrokerChannel.objects.filter(is_user=True):
            try:
                temp_channel_message_object = await client.send_message(broker_user.group_id, final_data)
                question = f"{temp_channel_message_object.chat.id}-{temp_channel_message_object.id}"

                # await Conversations.objects.filter(user_id=broker_user.group_id, question=question).adelete()
                # await Conversations.objects.acreate(
                #     user_id=broker_user.group_id,
                #     question=question,
                #     conversation_type="bot message",
                # )

                await Conversations.objects.aget_or_create(
                    user_id=broker_user.group_id,
                    question=question,
                    conversation_type="bot message",
                )

            except Exception as e:
                continue

    except BadRequest as e:
        logging.exception(e)


@Client.on_message(filters.private, group=1)
async def response_to_bots_test(client, message):
    if not message.text:
        return None

    user_id = message.from_user.id
    response = message.text.strip()

    question_answered_to_object = await Conversations.objects.filter(
        user_id=user_id, response="", conversation_type="bot message"
    ).afirst()

    if not question_answered_to_object:
        # this user doesnt have a question that needs answer
        message.continue_propagation()
        return None

    channel_id, message_id = question_answered_to_object.question.split("-")

    await Conversations.objects.filter(id=question_answered_to_object.id).adelete()

    channel_id = int(channel_id)
    message_id = int(message_id)
    print(response)


@Client.on_callback_query(filters.regex("CANCEL"))
async def user_cancel(client, callback_query):
    await callback_query.answer(cache_time=100)
    await callback_query.message.edit_text(callback_query.message.text.html, reply_markup=None)

    await Conversations.objects.filter(user_id=callback_query.from_user.id).adelete()

    response_to_user = "Your request has been cancelled\n" + "To start a new quote send /newquote again"
    await client.send_message(callback_query.message.chat.id, response_to_user)
