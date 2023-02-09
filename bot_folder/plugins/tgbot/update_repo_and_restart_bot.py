from os import execvp
import sys
import subprocess

from pyrogram import Client, filters

from shared_config import shared_object


SUPER_ADMIN = shared_object.clients["super_admin"]


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("restart_bot", prefixes="!"))
async def restart(client, message):
    # sys.executable
    # A string giving the absolute path of the executable binary for the Python interpreter like venv/bin/python3.11
    # print(sys.executable)
    await message.reply("Restarting the bot with latest commit")
    execvp(sys.executable, [sys.executable, "-m", "bot_folder"])


@Client.on_message(filters.user(SUPER_ADMIN) & filters.command("update_repo", prefixes="!"))
async def update_repo(client, message):
    try:
        out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
    except Exception as e:
        return await message.reply_text(str(e))

    else:
        if "Already up to date." in str(out):
            return await message.reply_text("Its already up-to date!")
        else:
            await message.reply_text(f"```{out}```")
            await restart(client, message)
