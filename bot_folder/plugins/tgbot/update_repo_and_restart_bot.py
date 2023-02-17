from os import execvp
import sys
import subprocess

from pyrogram import Client, filters

from shared_config import shared_object


@Client.on_message(filters.user(shared_object.clients["super_admin"]) & filters.command("restart_bot", prefixes="!"))
async def restart(client, message):
    """
    This is a message handler that is used to restart the bot
    The user must be super admin in order use this command.
    The command syntax is: !restart_bot
    """

    # sys.executable
    # A string giving the absolute path of the executable binary for the Python interpreter like venv/bin/python3.11
    # print(sys.executable)

    # Get the absolute path of the executable binary for the Python interpreter
    # This can be used to start a new instance of the bot

    await message.reply("Restarting the bot with latest commit")

    # Start a new instance of the bot using the same Python interpreter and the "bot_folder" module
    # The execvp() function replaces the current process with a new process
    # that runs the specified command ("python", "-m", "bot_folder")
    # This is a more reliable way to restart the bot than calling os.system() or subprocess.call()

    execvp(sys.executable, [sys.executable, "-m", "bot_folder"])


@Client.on_message(filters.user(shared_object.clients["super_admin"]) & filters.command("update_repo", prefixes="!"))
async def update_repo(client, message):
    """
    This is a message handler that is used to  update the bot code by pulling latest commit from a remote repository
    The user must be super admin in order use this command.
    The command syntax is: !update_repo
    """

    try:
        # Run the `git pull` command to pull the latest changes from the repository
        out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
    except Exception as e:
        # If there is an error, return the error message to the user
        return await message.reply_text(str(e))

    else:
        if "Already up to date." in str(out):
            return await message.reply_text("Its already up-to date!")
        else:
            await message.reply_text(f"```{out}```")
            await restart(client, message)
