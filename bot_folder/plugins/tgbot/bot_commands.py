from pyrogram import Client, filters

from db.models import (
    Questions,
    Conversations,
    ConversationIdentifier,
    ConversationBackups,
)
from datetime import datetime, timezone
from bot_folder.helpers import add_keyboad_button_and_send_text_message


@Client.on_message(filters.private & filters.command("start", prefixes="/"))
async def start(client, message):
    name = f"{message.from_user.first_name} {(message.from_user.last_name or '')}"
    user_id = message.from_user.id
    mention = f"[{name}](tg://user?id={user_id})"

    greetings = f"Hey {mention} thank you for reaching out for a quote request, please click /newquote below and fill out all the information, the quote request will propagate to our network of trusted brokers with solid reputations, and we will get back to you wit the best options as soon as possible."

    await message.reply(greetings)
    message.stop_propagation()


@Client.on_message(filters.private & filters.command("newquote", prefixes="/"))
async def newquote(client, message):
    user_id = message.from_user.id
    await Conversations.objects.filter(user_id=user_id).adelete()

    QUERY = []
    async for question_data in Questions.objects.all().order_by("question_order"):
        QUERY.append(
            Conversations(user_id=user_id, question_order=question_data.question_order, question=question_data.question)
        )
    await Conversations.objects.abulk_create(QUERY)

    await first_question(client, message)
    message.stop_propagation()


async def first_question(client, message):
    # first question
    user_id = message.from_user.id
    question = await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()
    if question:
        await message.reply(question.question)

    message.stop_propagation()


@Client.on_message(filters.private, group=1)
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
        await message.reply("Send /newquote for new quote request")
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

        name = f""
        user_id = message.from_user.id
        mention = f"[{message.from_user.first_name} {(message.from_user.last_name or '')}](tg://user?id={user_id})"

        final_data = (
            f"Date: {added_time.strftime('%d %b %Y at %H:%M:%S %Z')}\n"
            f"UserID: {user_id}\n"
            f"Name: [{message.from_user.first_name} {(message.from_user.last_name or '')}](tg://user?id={user_id})\n"
            f"Username: {'@' + message.from_user.username if message.from_user.username else None}\n\n"
        )

        final_data += "\n".join(question_answer)
        await add_keyboad_button_and_send_text_message(client, user_id, final_data, "SUBMIT", "SUBMIT")
