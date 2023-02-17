from io import BytesIO
import subprocess

from pyrogram import Client, filters

from shared_config import shared_object


def execute_python_code_function(code):
    # Run the django shell command using the subprocess module
    p = subprocess.Popen(['python', 'manage.py', 'shell', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Get the output and error messages from the subprocess
    output, error = p.communicate()

    # Combine the output and error messages into a single string
    result = f"OUTPUT\n\n{output.decode()}\nERROR\n\n{error.decode()}".strip()

    # Write the result string to a temporary file
    temp_file = BytesIO()
    temp_file.name = "result.txt"
    temp_file.write(result.encode())

    return temp_file


@Client.on_message(filters.user(shared_object.clients["super_admin"]) & filters.command("list_models", prefixes="!"))
async def models(client, message):
    """
    This is a message handler that list all the models with fields in the database.
    The user must be super admin in order use this command.
    The command syntax is: !list_models
    """

    # This is done instead of just calling list_models inside this function as django cant call sync code from async
    # Django: SynchronousOnlyOperation: You cannot call this from an async context - use a thread or sync_to_async

    # Define the Python code to be executed

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

    # Execute the Python code and get the output as a temporary file
    temp_file = execute_python_code_function(code)

    # Send the file as a reply to the user's message
    await message.reply_document(temp_file)

    message.stop_propagation()


@Client.on_message(filters.user(shared_object.clients["super_admin"]) & filters.command("orm", prefixes="!"))
async def orm(client, message):
    """
    This is a message handler that runs any code from django shell
    The user must be super admin in order use this command.
    The command syntax is: !orm code
    """

    # Extract code from the message
    message_text: str = message.text.replace("!orm", "", 1).strip()

    if message_text == "":
        # If the command argument is empty, inform the user and return
        await message.reply("add command")
        return None

    code = "from db.models import *\n" + message_text

    # Execute the Python code and get the output as a temporary file
    temp_file = execute_python_code_function(code)

    await message.reply_document(temp_file)

    message.stop_propagation()
