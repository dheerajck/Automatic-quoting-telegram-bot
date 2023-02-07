from pyrogram import Client, filters

from db.models import (
    Questions,
    Conversations,
    ConversationIdentifier,
    ConversationBackups,
)
from datetime import datetime, timezone
from bot_folder.helpers import add_keyboad_button_and_send_text_message


@Client.on_message(filters.private & filters.command("start", prefixes="!"))
async def start(client, message):
    user_id = message.from_user.id
    await message.reply("Hi")
    await Conversations.objects.filter(user_id=user_id).adelete()

    QUERY = []
    async for question_data in Questions.objects.all().order_by("question_order"):
        QUERY.append(
            Conversations(user_id=user_id, question_order=question_data.question_order, question=question_data.question)
        )
    await Conversations.objects.abulk_create(QUERY)

    await first_question(client, message)


async def first_question(client, message):
    # first question
    user_id = message.from_user.id
    question = await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()
    await message.reply(question.question)


@Client.on_message(filters.private)
async def questionaire(client, message):
    user_id = message.from_user.id
    if not message.text:
        return None

    response = message.text
    # question that was asked before, if there was a question left to ask
    question_answered_to_object = (
        await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()
    )

    if not question_answered_to_object:
        # this user doesnt have a question that needs answer
        await message.reply("send start")
        return None

    # add answer to the question as response in Conversations table
    await Conversations.objects.filter(id=question_answered_to_object.id).aupdate(response=response)

    # next question to ask if there is a question to  left to ask
    next_question_object = (
        await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()
    )

    if next_question_object:
        # asking question
        await message.reply(next_question_object.question)
    else:
        # this user have answered all the questions
        # backing up conversations details
        added_time = datetime.now(timezone.utc)
        conversation_key = await ConversationIdentifier.objects.acreate(user_id=user_id, added=added_time)

        QUERY = []
        question_answer = []

        async for conversation_data in Conversations.objects.filter(user_id=user_id).order_by("question_order"):
            question_answer.append(f"{conversation_data.question}\n{conversation_data.response}\n")
            QUERY.append(
                ConversationBackups(
                    conversation_identifier=conversation_key,
                    question_order=conversation_data.question_order,
                    question=conversation_data.question,
                    response=conversation_data.response,
                )
            )

        await ConversationBackups.objects.abulk_create(QUERY)
        await Conversations.objects.filter(user_id=user_id).adelete()

        final_data = (
            f"Date: {added_time.strftime('%d %b %Y at %H:%M:%S %Z')}\n"
            f"UserID: {user_id}\n"
            f"Name: {message.from_user.first_name} {message.from_user.last_name or ''}\n"
            f"Username: {message.from_user.username or None}\n\n"
        )

        final_data += "\n".join(question_answer)
        await add_keyboad_button_and_send_text_message(client, user_id, final_data, "SUBMIT", "SUBMIT")
