#  Copyright (c) 2025 AshokShau
#  Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html
#  Part of the TgMusicBot project. All rights reserved where applicable.


from typing import ClassVar, TypedDict

from cachetools import TTLCache
from pytdbot import types

from ._config import config


class DownloadMetadata(TypedDict):
    chat_id: int
    remote_file_id: str
    filename: str
    message_id: int


class Telegram:
    """A helper class for processing and validating playable media from Telegram.

    This class provides methods to check if a Telegram message contains
    supported media (audio or video), extract file information, and manage
    a cache for downloaded media metadata.

    Attributes:
        UNSUPPORTED_TYPES (tuple): A tuple of `pytdbot.types` that are not
            considered playable media.
        MAX_FILE_SIZE (int): The maximum allowed file size for media, sourced
            from the bot's configuration.
        DownloaderCache (TTLCache): A time-to-live cache to store metadata
            of recently processed files.
    """

    UNSUPPORTED_TYPES = (
        types.MessageText,
        types.MessagePhoto,
        types.MessageSticker,
        types.MessageAnimation,
    )
    MAX_FILE_SIZE = config.MAX_FILE_SIZE
    DownloaderCache: ClassVar[TTLCache[str, DownloadMetadata]] = TTLCache[
        str, DownloadMetadata
    ](maxsize=5000, ttl=600)

    def __init__(self) -> None:
        """Initializes the Telegram helper."""
        self._file_info: tuple[int, str] | None = None

    @staticmethod
    def _extract_file_info(content: types.MessageContent | None) -> tuple[int, str]:
        """Extracts file size and name from various Telegram message content types.

        Args:
            content (types.MessageContent): The content object from a
                `pytdbot.types.Message`.

        Returns:
            tuple[int, str]: A tuple containing the file size in bytes and the
                filename. Returns (0, "UnknownMedia") for unsupported types.
        """
        media: (
            types.Video
            | types.Audio
            | types.VoiceNote
            | types.VideoNote
            | types.Document
            | None
        )
        media = None
        filename = "UnknownMedia"
        file: types.File | None = None
        if isinstance(content, types.MessageVideo) and content.video:
            media = content.video
            file = media.video
            filename = media.file_name or "Video.mp4"
        elif isinstance(content, types.MessageAudio) and content.audio:
            media = content.audio
            file = media.audio
            filename = media.file_name or "Audio.mp3"
        elif isinstance(content, types.MessageVoiceNote) and content.voice_note:
            file = content.voice_note.voice
            filename = "VoiceNote.ogg"
        elif isinstance(content, types.MessageVideoNote) and content.video_note:
            file = content.video_note.video
            filename = "VideoNote.mp4"
        elif isinstance(content, types.MessageDocument) and content.document:
            media = content.document
            if (media.mime_type or "").lower().startswith(("audio/", "video/")):
                file = media.document
                filename = media.file_name or "Document.mp4"
        return (file.size or 0, filename) if file is not None else (0, "UnknownMedia")

    def is_valid(self, msg: types.Message | None) -> bool:
        """Checks if a message contains a valid, playable media file.

        A message is considered valid if it's not an error, contains a
        supported media type, and its file size is within the allowed limit.

        Args:
            msg (Optional[types.Message]): The message to validate.

        Returns:
            bool: True if the message contains valid media, False otherwise.
        """
        if not msg or isinstance(msg, types.Error):
            return False

        content = msg.content
        if isinstance(content, self.UNSUPPORTED_TYPES):
            return False

        file_size, _ = self._extract_file_info(content)
        return 0 < file_size <= self.MAX_FILE_SIZE

    async def download_msg(
        self, dl_msg: types.Message, message: types.Message
    ) -> tuple[types.Error | types.LocalFile, str]:
        """Downloads the media from a message and caches its metadata.

        Before downloading, it validates the message using `is_valid`. If valid,
        it proceeds with the download, stores metadata in the cache, and
        returns the download result.

        Args:
            dl_msg (types.Message): The message containing the media to download.
            message (types.Message): The original message that triggered the
                download, used for context (e.g., chat_id).

        Returns:
            tuple[Union[types.Error, types.LocalFile], str]: A tuple containing
                the download result (either a `LocalFile` object or an `Error`)
                and the filename.
        """
        if not self.is_valid(dl_msg):
            return (
                types.Error(code=0, message="Invalid or unsupported media file."),
                "InvalidMedia",
            )

        unique_id = dl_msg.remote_unique_file_id
        remote_id = dl_msg.remote_file_id
        if (
            not unique_id
            or not remote_id
            or message.chat_id is None
            or message.id is None
        ):
            return types.Error(
                code=400, message="Missing file or message metadata"
            ), "InvalidMedia"
        chat_id = message.chat_id
        _file_size, file_name = self._extract_file_info(dl_msg.content)

        if unique_id not in Telegram.DownloaderCache:
            Telegram.DownloaderCache[unique_id] = {
                "chat_id": chat_id,
                "remote_file_id": remote_id,
                "filename": file_name,
                "message_id": message.id,
            }
        return await dl_msg.download(), file_name

    @staticmethod
    def get_cached_metadata(
        unique_id: str,
    ) -> DownloadMetadata | None:
        """Retrieves cached metadata for a file.

        Args:
            unique_id (str): The remote unique file ID of the media.

        Returns:
            Optional[dict]: The cached metadata dictionary, or None if not found.
        """
        return Telegram.DownloaderCache.get(unique_id)

    @staticmethod
    def clear_cache(unique_id: str) -> DownloadMetadata | None:
        """Removes an item from the metadata cache.

        Args:
            unique_id (str): The remote unique file ID to remove from the cache.
        """
        return Telegram.DownloaderCache.pop(unique_id, None)


tg = Telegram()
