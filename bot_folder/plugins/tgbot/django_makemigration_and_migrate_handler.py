from io import BytesIO
import subprocess

from pyrogram import Client, filters

from shared_config import shared_object


@Client.on_message(filters.user(shared_object.clients["super_admin"]) & filters.command("makemigration", prefixes="!"))
async def makemigration_handler(client, message):
    """
    This is a message handler that creates a new migration file for the database.
    The user must be super admin in order use this command.
    The command syntax is: !makemigration
    """

    # Run the django makemigrations command using the subprocess module
    p = subprocess.Popen(
        ['python', 'manage.py', 'makemigrations', 'db'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Get the output and error messages from the subprocess
    output, error = p.communicate()

    # Combine the output and error messages into a single string
    result = f"OUTPUT\n\n{output.decode()}\nERROR\n\n{error.decode()}".strip()

    # Write the result string to a temporary file
    temp_file = BytesIO()
    temp_file.name = "result.txt"
    temp_file.write(result.encode())

    # Reply to the user with the temporary file
    await message.reply_document(temp_file)

    message.stop_propagation()


@Client.on_message(filters.user(shared_object.clients["super_admin"]) & filters.command("migrate", prefixes="!"))
async def migrate_handler(client, message):
    """
    This is a message handler that applies any pending database migrations to the database.
    The user must be super admin in order use this command.
    The command syntax is: !migrate
    """

    # Run the django migrate command using the subprocess module
    p = subprocess.Popen(
        ['python', 'manage.py', 'migrate'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Get the output and error messages from the subprocess
    output, error = p.communicate()

    # Combine the output and error messages into a single string
    result = f"OUTPUT\n\n{output.decode()}\nERROR\n\n{error.decode()}".strip()

    # Write the result string to a temporary file
    temp_file = BytesIO()
    temp_file.name = "result.txt"
    temp_file.write(result.encode())

    # Reply to the user with the temporary file
    await message.reply_document(temp_file)

    message.stop_propagation()
