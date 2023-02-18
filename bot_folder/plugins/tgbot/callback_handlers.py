import logging
from datetime import datetime, timezone

from pyrogram import Client, filters
from pyrogram.errors import BadRequest, Forbidden

from db.models import AdminChannel, BrokerChannel, Conversations
from db.models import (
    ConversationIdentifier,
    ConversationBackups,
)

from bot_folder.helpers import add_keyboad_button_and_send_text_message


async def extract_quote_and_time_data(final_message):
    """
    Extract quote id and added time in utc from final message which is in markdown format
    """

    # Get final message to which user pressed submit button with proper markdown formating
    final_message = final_message.strip()
    final_message = final_message.split("\n")

    # extract quote id
    quote_id = final_message[0].strip()
    quote_id = quote_id.replace("Quote ID:", "").strip()

    # Removes quote id and create the message srting which was used to hash to find quote id using xxhash
    # We can avoid this but choose to keep this

    # remove quote id
    final_message = final_message[1:]
    final_message = "\n".join(final_message)
    final_message = final_message.strip()

    # Extract added time from the message and convert it to a datetime object in UTC

    added_time_str = final_message.split("\n")[0].replace("Date:", "").strip()

    added_time_str = final_message.split("\n")[0].replace("Date:", "").strip()
    added_time = datetime.strptime(added_time_str, '%d %b %Y at %H:%M:%S %Z')
    added_time = added_time.replace(tzinfo=timezone.utc)

    return quote_id, added_time


@Client.on_callback_query(filters.regex("SUBMIT"))
async def user_submit_callback_handler(client, callback_query):
    """
    This message handler handles the callback query when a user press SUBMIT button
    after answering all the questions
    """

    await callback_query.answer(cache_time=100)

    # Edit message to remove inline keyboard
    # await callback_query.message.edit_text(callback_query.message.text.html, reply_markup=None)

    await client.edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.id,
        reply_markup=None,
    )

    quote_id, added_time = await extract_quote_and_time_data(callback_query.message.text.markdown.strip())
    user_id = callback_query.from_user.id

    # Save conversation identifiers of this conversation in database
    conversation_key = await ConversationIdentifier.objects.acreate(
        user_id=user_id, added=added_time, quote_id=quote_id
    )

    # Save conversation details in ConversationBackups table
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

    # Delete conversations from Conversations table
    await Conversations.objects.filter(user_id=user_id).adelete()

    # Reply to the user with confirmation message
    response_to_user = (
        "Thank you for your request, we have begun sourcing the best offers across the verified brokers network, and will get back to you as soon as possible.\n"
        "To start a new quote send /newquote again"
    )

    # Send the quote request message to admins
    await client.send_message(callback_query.message.chat.id, response_to_user)

    # Send another message with Quote id included with `SEND` button which allow admin
    # to send the quote request to broker channels
    interaction_question_with_quote_id = (
        f"Quote ID: {quote_id}\n\n" + "Do you want to send this quote to broker channels ??"
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


@Client.on_callback_query(filters.regex("CANCEL"))
async def user_cancel_callback_handler(client, callback_query):
    """
    This message handler handles the callback query when a user press CANCEL button
    after answering all the questions
    """
    await callback_query.answer(cache_time=100)

    # Edit message to remove inline keyboard
    await client.edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.id,
        reply_markup=None,
    )

    # Delete the conversation object from the database
    await Conversations.objects.filter(user_id=callback_query.from_user.id).adelete()

    # Reply to the user to inform request is cancelled
    response_to_user = "Your request has been cancelled\n" + "To start a new quote send /newquote again"
    await client.send_message(callback_query.message.chat.id, response_to_user)


@Client.on_callback_query(filters.regex(r"SEND"))
async def admin_choice_callback_handler(client, callback_query):
    """
    This message handler handles the callback query when an admin press SEND button
    to a quote request message in admin channel
    """

    await callback_query.answer(cache_time=100)

    # Edit the message and remove the keyboard.
    await client.edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.id,
        reply_markup=None,
    )

    # Get the quote ID from the message.
    final_message = callback_query.message.text
    quote_id = final_message.split("\n")[0].strip()
    quote_id = quote_id.replace("Quote ID:", "").strip()

    # Get the questions and answers for the quote from db without private questions
    # to send it on broker channels using quote_id
    question_answer = []
    conversation_identifier_object = await ConversationIdentifier.objects.filter(quote_id=quote_id).afirst()

    async for conversation_backup in ConversationBackups.objects.filter(
        conversation_identifier=conversation_identifier_object.id
    ).exclude(private_question=True):
        question_answer.append(f"{conversation_backup.question}\n{conversation_backup.response}\n")

    # Create new text message with the quote ID and retrieved questions and answers.
    final_data = "\n".join(question_answer)
    final_data = f"Quote ID: {quote_id}\n\n" + final_data

    # Get the broker channel object for the admin.(main one)
    admin_broker_channel = await BrokerChannel.objects.filter(is_user=False).afirst()

    try:
        # Send the quote to the broker channel.
        temp_message = await client.send_message(admin_broker_channel.group_id, final_data)

        # Reply to the admin with confirmation message that the message is send to broker channel with link
        response = f"Quote sent to broker channel ([link of message in broker channel]({temp_message.link}))"
        await client.send_message(callback_query.message.chat.id, response)

        # Send the quote to all the broker users
        async for broker_user in BrokerChannel.objects.filter(is_user=True):
            try:
                await client.send_message(broker_user.group_id, final_data)

                # Custom question
                question = quote_id

                # await Conversations.objects.filter(user_id=broker_user.group_id, question=question).adelete()
                # await Conversations.objects.acreate(
                #     user_id=broker_user.group_id,
                #     question=question,
                #     conversation_type="bot message",
                # )

                # Add a conversation object with conversation_type bot message to Conversations table
                # as we expect a response from brokers
                await Conversations.objects.aget_or_create(
                    user_id=broker_user.group_id,
                    question=question,
                    conversation_type="bot message",
                )

            except Exception as e:
                # Ignore the error and move on if bot cant pm a broker,
                # users should pm bot first and shouldnt block bot
                continue

    except BadRequest as e:
        logging.exception(e)


@Client.on_message(filters.private, group=1)
async def response_from_brokers_test(client, message):
    """
    This message handler handles user responses
    to quote message shared by bot
    """

    # Ignore responses that are not text message
    if not message.text:
        message.continue_propagation()

    user_id = message.from_user.id
    name = message.from_user.first_name + (message.from_user.last_name or "")

    # Checks if there is a question that bot is expecting answers from this user <message.from_chat.id>
    question_answered_to_object = await Conversations.objects.filter(
        user_id=user_id, response="", conversation_type="bot message"
    ).afirst()

    if not question_answered_to_object:
        # This user doesnt have a question that needs answer
        await message.reply("Send /newquote for new quote request")
        message.continue_propagation()
        return None

    # Get quote id from the question string(Custom question)
    # and then delete this question from the Conversations table

    question = quote_id = question_answered_to_object.question.strip()
    response = message.text.strip()

    await Conversations.objects.filter(id=question_answered_to_object.id).adelete()

    quote_conversation = await ConversationIdentifier.objects.filter(quote_id=quote_id).afirst()
    discussion_group_id = quote_conversation.discussion_group_id
    message_id = quote_conversation.message_id

    response = f"{name} replied\n{response}"
    try:
        await client.send_message(chat_id=discussion_group_id, reply_to_message_id=message_id, text=response)
    except Exception as e:
        pass

    await message.reply("Thanks for your response")

    message.continue_propagation()


@Client.on_message(filters.group)
async def discussion_group(client, message):
    """
    This message handler handles message from discussion group of first broker channel
    """

    if message.sender_chat:
        fist_broker_channel_object = await BrokerChannel.objects.filter(
            group_id=message.sender_chat.id, is_user=False
        ).afirst()

        if fist_broker_channel_object.group_id == message.sender_chat.id:
            discussion_group_id = message.chat.id
            message_id = message.id
            final_message = message.text.strip()
            quote_id = final_message.split("\n")[0].strip()
            quote_id = quote_id.replace("Quote ID:", "").strip()
            await ConversationIdentifier.objects.filter(quote_id=quote_id).aupdate(
                discussion_group_id=discussion_group_id, message_id=message_id
            )
