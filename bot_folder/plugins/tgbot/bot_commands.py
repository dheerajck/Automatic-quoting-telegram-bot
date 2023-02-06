from pyrogram import Client, filters

from db.models import (
    Questions,
    Conversations,
    ConversationIdentifier,
    ConversationBackups,
    AdminChannel,
    BrokerChannel,
)
from datetime import datetime, timezone


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

    async for i in Conversations.objects.all():
        print(i.user_id, i.question, i.question_order, i.response)

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
        QUERY = []
        conversation_key = await ConversationIdentifier.objects.acreate(
            user_id=user_id, added=datetime.now(timezone.utc)
        )
        async for conversation_data in Conversations.objects.filter(user_id=user_id).order_by("question_order"):
            QUERY.append(
                ConversationBackups(
                    conversation_identifier=conversation_key,
                    question_order=conversation_data.question_order,
                    question=conversation_data.question_order,
                    response=conversation_data.response,
                )
            )
        await ConversationBackups.objects.abulk_create(QUERY)
        await message.reply("done")
