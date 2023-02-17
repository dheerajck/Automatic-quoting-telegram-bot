from pyrogram import Client, filters

from django.utils import timezone
from db.models import Questions, Conversations

from bot_folder.helpers import add_keyboad_button_and_send_text_message
from bot_folder.helpers import does_input_string_match_pattern


@Client.on_message(filters.private & filters.command("start", prefixes="/"))
async def start(client, message):
    name = f"{message.from_user.first_name} {(message.from_user.last_name or '')}"
    user_id = message.from_user.id
    mention = f"[{name}](tg://user?id={user_id})"

    greetings = (
        f"Hey {mention}, thank you for reaching out for a quote request, "
        "please click /newquote below and fill out all the information, "
        "the quote request will propagate to our network of trusted brokers with solid reputations, "
        "and we will get back to you wit the best options as soon as possible."
    )

    await message.reply(greetings)
    message.stop_propagation()


@Client.on_message(filters.private & filters.command("newquote", prefixes="/"))
async def newquote(client, message):
    user_id = message.from_user.id
    await Conversations.objects.filter(user_id=user_id).adelete()

    QUERY = []
    async for question_data in Questions.objects.all().order_by("question_order"):
        QUERY.append(
            Conversations(
                user_id=user_id,
                question_order=question_data.question_order,
                question=question_data.question,
                regex_pattern=question_data.regex_pattern,
                invalid_response=question_data.invalid_response,
                private_question=question_data.private_question,
            )
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

    response = message.text.strip()
    # question that was asked before, if there was a question left to ask
    question_answered_to_object = (
        await Conversations.objects.filter(user_id=user_id, response="", conversation_type="questionaire")
        .order_by("question_order")
        .afirst()
    )

    if not question_answered_to_object:
        # this user doesnt have a question that needs answer
        message.continue_propagation()
        # await message.reply("Send /newquote for new quote request")
        # return None

    # print(question_answered_to_object.question, question_answered_to_object.regex_pattern)

    if question_answered_to_object.regex_pattern:
        if not await does_input_string_match_pattern(response, question_answered_to_object.regex_pattern):
            await message.reply(question_answered_to_object.invalid_response)
            return None

    # add answer to the question as response in Conversations table
    await Conversations.objects.filter(id=question_answered_to_object.id).aupdate(response=response)

    # next question to ask if there is a question to  left to ask
    next_question_object = (
        await Conversations.objects.filter(user_id=user_id, response="", conversation_type="questionaire")
        .order_by("question_order")
        .afirst()
    )

    if next_question_object:
        # asking question
        await message.reply(next_question_object.question)
    else:
        # this user have answered all the questions
        # backing up conversations details

        added_time = timezone.now()

        question_answer = []

        async for conversation_data in Conversations.objects.filter(
            user_id=user_id, conversation_type="questionaire"
        ).order_by("question_order"):
            question_answer.append(f"{conversation_data.question}\n{conversation_data.response}\n")

        user_id = message.from_user.id

        final_data = (
            f"Date: {added_time.strftime('%d %b %Y at %H:%M:%S %Z')}\n"
            f"UserID: `{user_id}`\n"
            f"Name: [{message.from_user.first_name} {(message.from_user.last_name or '')}](tg://user?id={user_id})\n"
            f"Username: {'@' + message.from_user.username if message.from_user.username else None}\n\n"
        )

        final_data += "\n".join(question_answer)
        final_data = final_data.strip()

        await add_keyboad_button_and_send_text_message(
            client, user_id, final_data, {"SUBMIT": "SUBMIT", "CANCEL": "CANCEL"}
        )
