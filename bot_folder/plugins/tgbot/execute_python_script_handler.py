from io import BytesIO
import subprocess

from pyrogram import Client, filters

from shared_config import shared_object


SUPER_ADMIN = shared_object.clients["super_admin"]


def execute_python_code_function(code):
    p = subprocess.Popen(['python', 'manage.py', 'shell', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = p.communicate()

    result = f"OUTPUT\n\n{output.decode()}\nERROR\n\n{error.decode()}".strip()

    temp_file = BytesIO()
    temp_file.name = "result.txt"
    temp_file.write(result.encode())

    return temp_file


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("models", prefixes="!"))
async def models(client, message):
    message_text: str = message.text.replace("!orm", "", 1).strip()
    if message_text == "":
        await message.reply("add command")
        return None

    # This is done instead of just calling list_models inside this function as django cant call sync code from async
    # Django: SynchronousOnlyOperation: You cannot call this from an async context - use a thread or sync_to_async

    code = """
def list_models():
    from django.db import connection

    tables = connection.introspection.table_names()
    seen_models = connection.introspection.installed_models(tables)
    for i in seen_models:
        print(i)
        print([f.name for f in i._meta.get_fields()])

    return tables

list_models()
"""

    temp_file = execute_python_code_function(code)
    await message.reply_document(temp_file)


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("orm", prefixes="!"))
async def orm(client, message):
    message_text: str = message.text.replace("!orm", "", 1).strip()

    if message_text == "":
        await message.reply("add command")
        return None

    code = "from db.models import *\n" + message_text

    temp_file = execute_python_code_function(code)
    await message.reply_document(temp_file)
