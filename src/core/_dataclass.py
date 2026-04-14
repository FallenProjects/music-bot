#  Copyright (c) 2025 AshokShau
#  Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html
#  Part of the TgMusicBot project. All rights reserved where applicable.

from pathlib import Path
from typing import Union, List, Optional

from pydantic import BaseModel


class CachedTrack(BaseModel):
    """Represents a track that is cached for playback.

    Attributes:
        url (str): The URL of the track.
        name (str): The name of the track.
        loop (int): The number of times the track should be looped.
        user (str): The user who requested the track.
        file_path (Union[str, Path]): The local file path of the track.
        thumbnail (str): The URL or local path of the track's thumbnail.
        track_id (str): A unique identifier for the track.
        duration (int): The duration of the track in seconds.
        is_video (bool): A flag indicating if the track is a video.
        platform (str): The platform from which the track originated.
    """

    url: str
    name: str
    loop: int
    user: str
    file_path: Union[str, Path]
    thumbnail: str
    track_id: str
    duration: int = 0
    is_video: bool
    platform: str

class TrackInfo(BaseModel):
    """Holds detailed information about a specific track."""
    id: str
    url: str
    cdnurl: str
    key: Optional[str] = None
    platform: str


class MusicTrack(BaseModel):
    """Represents a single music track returned from a search query."""
    title: str
    id: str
    url: str
    thumbnail: str
    duration: int
    channel: Optional[str]
    views: Optional[str]
    platform: str


class PlatformTracks(BaseModel):
    """Collection of music tracks."""
    results: List[MusicTrack]
