#  Copyright (c) 2025 AshokShau
#  Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html
#  Part of the TgMusicBot project. All rights reserved where applicable.


from typing import Literal

from pytdbot import types

from ._config import config

CLOSE_BTN = types.InlineKeyboardButton(
    text="Cʟᴏsᴇ", type=types.InlineKeyboardButtonTypeCallback(data=b"vcplay_close")
)


def control_buttons(
    mode: Literal["play", "pause", "resume"],
) -> types.ReplyMarkupInlineKeyboard:
    """Generates an inline keyboard for player controls based on the current state.

    This function creates a dynamic set of control buttons (skip, stop, pause,
    resume) tailored to the current playback mode.

    Args:
        mode (Literal["play", "pause", "resume"]): The current playback state.
            - "play": Shows all controls including pause.
            - "pause": Shows controls with a resume button instead of pause.
            - "resume": Shows controls with a pause button instead of resume.

    Returns:
        types.ReplyMarkupInlineKeyboard: An inline keyboard object with the
            appropriate control buttons.
    """

    def btn(text: str, name: str) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(
            text=text,
            type=types.InlineKeyboardButtonTypeCallback(data=f"play_{name}".encode()),
        )

    skip_btn = btn("‣‣I", "skip")
    stop_btn = btn("▢", "stop")
    pause_btn = btn("II", "pause")
    resume_btn = btn("▷", "resume")

    layouts = {
        "play": [[skip_btn, stop_btn, pause_btn, resume_btn], [CLOSE_BTN]],
        "pause": [[skip_btn, stop_btn, resume_btn], [CLOSE_BTN]],
        "resume": [[skip_btn, stop_btn, pause_btn], [CLOSE_BTN]],
    }

    return types.ReplyMarkupInlineKeyboard(rows=layouts.get(mode, [[CLOSE_BTN]]))


CHANNEL_BTN = types.InlineKeyboardButton(
    text="ᴜᴘᴅᴀᴛᴇꜱ", type=types.InlineKeyboardButtonTypeUrl(url=config.SUPPORT_CHANNEL)
)

GROUP_BTN = types.InlineKeyboardButton(
    text="ꜱᴜᴘᴘᴏʀᴛ", type=types.InlineKeyboardButtonTypeUrl(url=config.SUPPORT_GROUP)
)

HELP_BTN = types.InlineKeyboardButton(
    text="Hᴇʟᴘ & Cᴏᴍᴍᴀɴᴅꜱ", type=types.InlineKeyboardButtonTypeCallback(data=b"help_all")
)

USER_BTN = types.InlineKeyboardButton(
    text="Uꜱᴇʀ Cᴏᴍᴍᴀɴᴅꜱ", type=types.InlineKeyboardButtonTypeCallback(data=b"help_user")
)

ADMIN_BTN = types.InlineKeyboardButton(
    text="Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅꜱ", type=types.InlineKeyboardButtonTypeCallback(data=b"help_admin")
)

OWNER_BTN = types.InlineKeyboardButton(
    text="Oᴡɴᴇʀ Cᴏᴍᴍᴀɴᴅꜱ", type=types.InlineKeyboardButtonTypeCallback(data=b"help_owner")
)

DEVS_BTN = types.InlineKeyboardButton(
    text="Dᴇᴠꜱ Cᴏᴍᴍᴀɴᴅꜱ", type=types.InlineKeyboardButtonTypeCallback(data=b"help_devs")
)

HOME_BTN = types.InlineKeyboardButton(
    text="Hᴏᴍᴇ", type=types.InlineKeyboardButtonTypeCallback(data=b"help_back")
)

SupportButton = types.ReplyMarkupInlineKeyboard(rows=[[CHANNEL_BTN, GROUP_BTN], [CLOSE_BTN]])

HelpMenu = types.ReplyMarkupInlineKeyboard(
    rows=[
        [USER_BTN, ADMIN_BTN],
        [OWNER_BTN, DEVS_BTN],
        [CLOSE_BTN, HOME_BTN],
    ]
)

BackHelpMenu = types.ReplyMarkupInlineKeyboard(rows=[[HELP_BTN, HOME_BTN], [CLOSE_BTN]])


# ─────────────────────
# Dynamic Keyboard Generator
# ─────────────────────


def add_me_markup(username: str) -> types.ReplyMarkupInlineKeyboard:
    """Creates the inline keyboard for the bot's start message.

    This keyboard includes a button to add the bot to a group, along with
    buttons for help, support, and updates.

    Args:
        username (str): The username of the bot, used to create the
            "add to group" link.

    Returns:
        types.ReplyMarkupInlineKeyboard: An inline keyboard object for the
            start message.
    """
    return types.ReplyMarkupInlineKeyboard(
        rows=[
            [
                types.InlineKeyboardButton(
                    text="Aᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    type=types.InlineKeyboardButtonTypeUrl(
                        url=f"https://t.me/{username}?startgroup=true"
                    ),
                ),
            ],
            [HELP_BTN],
            [CHANNEL_BTN, GROUP_BTN],
        ]
    )
