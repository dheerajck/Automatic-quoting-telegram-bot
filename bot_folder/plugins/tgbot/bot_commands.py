from pyrogram import Client, filters

from db.models import Questions, Conversations, AdminChannel, BrokerChannel


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
        return "No text message"

    response = message.text
    # current question if a question exist that user was asked
    question_answered_to_object = (
        await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()
    )
    # if there was no question that user has to answer now

    if not question_answered_to_object:
        await message.reply("send start")
        return None

        # question_count = await Questions.objects.all().acount()
        # answer_count = (
        #     await Conversations.objects.filter(user_id=user_id).exclude(response="").order_by("question_order").acount()
        # )
        # # if user has answered all questions
        # if question_count == answer_count:
        #     await message.reply("done")
        #     # remove from here and update somewhere
        #     return None

        # else:
        #     await message.reply("send start")
        #     return None

    await Conversations.objects.filter(id=question_answered_to_object.id).aupdate(response=response)

    next_question_object = (
        await Conversations.objects.filter(user_id=user_id, response="").order_by("question_order").afirst()
    )

    if next_question_object:
        await message.reply(next_question_object.question)
    else:
        await message.reply("done")
