from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def add_keyboad_button_and_send_text_message(client, user_id, text, keyboard_button, callback_data):
    await client.send_message(
        user_id,
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [  # First row
                    InlineKeyboardButton(keyboard_button, callback_data=callback_data),
                ],
            ]
        ),
    )
