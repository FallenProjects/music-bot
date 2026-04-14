# Copyright (c) 2025 AshokShau
# Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html
# Part of the TgMusicBot project. All rights reserved where applicable.


from pytdbot import Client, types

from src.core import Filter, admins_only, call, chat_cache

from .utils import sec_to_min
from .utils.play_helpers import extract_argument


@Client.on_message(filters=Filter.command("seek"))
@admins_only(is_bot=True, is_auth=True)
async def seek_song(_: Client, msg: types.Message) -> None:
    """Handles the /seek command to jump forward in the current track.

    This command allows an authorized user to seek a specified number of
    seconds forward from the current playback position.

    Usage:
        /seek [seconds]

    Args:
        _ (Client): The pytdbot client instance (unused).
        msg (types.Message): The message object containing the command.
    """
    chat_id = msg.chat_id
    if chat_id > 0:
        return

    curr_song = chat_cache.get_playing_track(chat_id)
    if not curr_song:
        await msg.reply_text("⏸ No track is currently playing.")
        return

    args = extract_argument(msg.text, enforce_digit=True)
    if not args:
        await msg.reply_text(
            "ℹ️ <b>Usage:</b> <code>/seek [seconds]</code>\n"
            "Example: <code>/seek 30</code> to jump 30 seconds forward"
        )
        return

    try:
        seek_time = int(args)
    except ValueError:
        await msg.reply_text("⚠️ Please enter a valid number of seconds.")
        return

    if seek_time < 0:
        await msg.reply_text("⚠️ Please enter a positive number of seconds.")
        return

    if seek_time < 20:
        await msg.reply_text("⚠️ Minimum seek time is 20 seconds.")
        return

    curr_dur = await call.played_time(chat_id)
    if isinstance(curr_dur, types.Error):
        await msg.reply_text(f"⚠️ <b>Error:</b> {curr_dur.message}")
        return

    seek_to = curr_dur + seek_time
    if seek_to >= curr_song.duration:
        max_duration = sec_to_min(curr_song.duration)
        await msg.reply_text(f"⚠️ Cannot seek beyond track duration ({max_duration}).")
        return

    _seek = await call.seek_stream(
        chat_id,
        curr_song.file_path,
        seek_to,
        curr_song.duration,
        curr_song.is_video,
    )
    if isinstance(_seek, types.Error):
        await msg.reply_text(f"⚠️ <b>Error:</b> {_seek.message}")
        return

    await msg.reply_text(
        f"⏩ Seeked {seek_time} seconds forward by {await msg.mention()}\n"
        f"🎵 Now at: {sec_to_min(seek_to)}/{sec_to_min(curr_song.duration)}"
    )
