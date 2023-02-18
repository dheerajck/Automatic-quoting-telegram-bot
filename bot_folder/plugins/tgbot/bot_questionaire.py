import xxhash

from pyrogram import Client, filters

from django.utils import timezone
from db.models import Questions, Conversations

from bot_folder.helpers import add_keyboad_button_and_send_text_message
from bot_folder.helpers import does_input_string_match_pattern


@Client.on_message(filters.private & filters.command("start", prefixes="/"))
async def start(client, message):
    """
    This is a message handler that sends a greeting message when a user sends /start in private chat
    The command syntax is: /start
    """

    # Construct a mention string using the user's first and last name.
    name = f"{message.from_user.first_name} {(message.from_user.last_name or '')}"
    user_id = message.from_user.id
    mention = f"[{name}](tg://user?id={user_id})"

    # Construct the greeting message.
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
    """
    This is a message handler that helps a user to request quote in private chat
    The command syntax is: /newquote

    It populates the Conversations table with a set of standard questions and removes any pending unanswered questions
    asked to the user <message.from_chat.id> and calls the `first_question` function to initiate the conversation.
    """

    # Delete any existing conversations associated with this user.
    user_id = message.from_user.id
    await Conversations.objects.filter(user_id=user_id).adelete()

    # Create new Conversations objects for each question in the Questions table.
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

    # Ask the first question.
    await first_question(client, message)
    message.stop_propagation()


async def first_question(client, message):
    """
    This function sends the first question
    to the user <message.from_chat.id>.
    """

    user_id = message.from_user.id

    # Get the first question for this user.
    question = await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()

    if question:
        await message.reply(question.question)

    message.stop_propagation()


@Client.on_message(filters.private, group=1)
async def questionaire(client, message):
    """
    This is a message handler that asks a series of questions to the user and stores their responses
    in the Conversations table. Once all the questions have been answered, user is presented with two buttons 'SUBMIT' and 'CANCEL'.
    If the user <message.from_chat.id> doesnt have any questions to answer, it ignores the message updates
    """

    user_id = message.from_user.id
    if not message.text:
        return None

    response = message.text.strip()

    # Get the question that was asked before, if there was a question asked to this user that needs an answer
    question_answered_to_object = (
        await Conversations.objects.filter(user_id=user_id, response="", conversation_type="questionaire")
        .order_by("question_order")
        .afirst()
    )

    if not question_answered_to_object:
        # This user doesn't have a question that needs answering
        # await message.reply("Send /newquote for new quote request")
        message.continue_propagation()
        # return None

    # print(question_answered_to_object.question, question_answered_to_object.regex_pattern)

    # Check if the user's response matches the expected pattern (if any)
    if question_answered_to_object.regex_pattern:
        # If users response isnt matching expected pattern, let the user know about that and ask to answer again
        if not await does_input_string_match_pattern(response, question_answered_to_object.regex_pattern):
            await message.reply(question_answered_to_object.invalid_response)
            return None

    # Update the user's response in the Conversations table
    await Conversations.objects.filter(id=question_answered_to_object.id).aupdate(response=response)

    # Get the next question if there is a question to  left to ask
    next_question_object = (
        await Conversations.objects.filter(user_id=user_id, response="", conversation_type="questionaire")
        .order_by("question_order")
        .afirst()
    )

    if next_question_object:
        # Asking next question to the user
        await message.reply(next_question_object.question)
    else:
        # This user has answered all the questions, so show them their responses with 'SUBMIT' and 'CANCEL' buttons
        added_time = timezone.now()
        question_answer = []

        # Construct final message with questions and the answers including users details.

        async for conversation_data in Conversations.objects.filter(
            user_id=user_id, conversation_type="questionaire"
        ).order_by("question_order"):
            question_answer.append(f"{conversation_data.question}\n{conversation_data.response}\n")

        final_data = (
            f"Date: {added_time.strftime('%d %b %Y at %H:%M:%S %Z')}\n"
            f"UserID: `{user_id}`\n"
            f"Name: [{message.from_user.first_name} {(message.from_user.last_name or '')}](tg://user?id={user_id})\n"
            f"Username: {'@' + message.from_user.username if message.from_user.username else None}\n\n"
        )

        final_data += "\n".join(question_answer)
        final_data = final_data.strip()

        # Generate a unique quote ID using the message content and a seed
        quote_id = xxhash.xxh32(final_data.encode("utf-8"), seed=12718745).hexdigest()

        final_data = f"Quote ID: {quote_id}\n\n" + final_data

        # Add SUBMIT AND CANCEL BUTTON to final message and send it to the user
        await add_keyboad_button_and_send_text_message(
            client, user_id, final_data, {"SUBMIT": "SUBMIT", "CANCEL": "CANCEL"}
        )
