#  Copyright (c) 2025 AshokShau
#  Licensed under the GNU AGPL v3.0: https://www.gnu.org/licenses/agpl-3.0.html
#  Part of the TgMusicBot project. All rights reserved where applicable.

import re
from pathlib import Path
from typing import Any, ClassVar

from pytdbot import types

from src.logger import LOGGER

from ._config import config
from ._dataclass import MusicTrack, PlatformTracks, TrackInfo
from ._downloader import MusicService
from ._httpx import http_client
from ._spotify_dl_helper import SpotifyDownload


class ApiData(MusicService):
    """Handles interactions with music streaming platform APIs.

    This class provides a unified interface to validate and process music URLs,
    retrieve track information, perform searches across different platforms,
    and download tracks. It supports platforms like Apple Music, Spotify, and
    SoundCloud.

    Attributes:
        URL_PATTERNS (dict): A dictionary of regular expression patterns for
            validating URLs from different platforms.
        query (Optional[str]): The URL or search term to be processed.
        api_url (Optional[str]): The base URL for the external API.
        api_key (Optional[str]): The API key for authenticating with the external API.
        client (HttpxClient): An HTTP client for making web requests.
    """

    # Platform URL validation patterns
    URL_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "apple_music": re.compile(
            r"^(https?://)?([a-z0-9-]+\.)*music\.apple\.com/"
            r"([a-z]{2}/)?"
            r"(album|playlist|song)/[a-zA-Z0-9\-._]+/(pl\.[a-zA-Z0-9]+|\d+)(\?.*)?$",
            re.IGNORECASE,
        ),
        "spotify": re.compile(
            r"^(https?://)?([a-z0-9-]+\.)*spotify\.com/"
            r"(track|playlist|album|artist)/[a-zA-Z0-9]+(\?.*)?$",
            re.IGNORECASE,
        ),
        "soundcloud": re.compile(
            r"^(https?://)?([a-z0-9-]+\.)*soundcloud\.com/"
            r"[a-zA-Z0-9_-]+(/(sets)?/[a-zA-Z0-9_-]+)?(\?.*)?$",
            re.IGNORECASE,
        ),
    }

    def __init__(self, query: str | None = None) -> None:
        """Initializes the ApiData instance.

        Args:
            query (Optional[str]): The URL or search term to process.
                Defaults to None.
        """
        self.query = self._sanitize_query(query) if query else None
        self.api_url = config.API_URL.rstrip("/") if config.API_URL else None
        self.api_key = config.API_KEY
        self.client = http_client

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Cleans and standardizes an input query string.

        This method removes URL fragments and surrounding whitespace while
        preserving query parameters such as Apple Music song identifiers.

        Args:
            query (str): The input string to sanitize.

        Returns:
            str: The sanitized query string.
        """
        return query.strip().split("#")[0]

    def is_valid(self) -> bool:
        """Validates if the query is a URL matching supported platform patterns.

        This method checks if the instance's query attribute is a valid and
        supported URL by comparing it against the predefined regex patterns.
        It also ensures that the API URL and key are configured.

        Returns:
            bool: True if the query is a valid URL for a supported platform,
                False otherwise.
        """
        if not self.query or not self.api_key or not self.api_url:
            return False

        return any(pattern.match(self.query) for pattern in self.URL_PATTERNS.values())

    async def _make_api_request(
        self, endpoint: str, params: dict[str, str] | None = None
    ) -> dict[str, Any] | None:
        """Makes a request to the external music API.

        Args:
            endpoint (str): The API endpoint to call.
            params (Optional[dict]): A dictionary of parameters to include in
                the request. Defaults to None.

        Returns:
            Optional[dict]: The JSON response from the API as a dictionary,
                or None if the request fails.
        """
        request_url = f"{self.api_url}/api/{endpoint.lstrip('/')}"
        return await self.client.make_request(request_url, params=params)

    async def get_info(self) -> PlatformTracks | types.Error:
        """Retrieves track information for a given URL.

        This method validates the URL and then queries the API to get
        metadata for the track, playlist, or album.

        Returns:
            Union[PlatformTracks, types.Error]: An object containing track
                metadata, or an Error object if the URL is invalid or the
                API request fails.
        """
        if not self.query or not self.is_valid():
            return types.Error(code=400, message="Invalid or unsupported URL provided")

        response = await self._make_api_request("get_url", {"url": self.query})
        return self._parse_tracks_response(response) or types.Error(
            code=404, message="No track information found"
        )

    async def search(self) -> PlatformTracks | types.Error:
        """Searches for tracks across supported platforms using a query.

        If the query is a valid URL, it fetches information directly. Otherwise,
        it performs a search using the provided query term.

        Returns:
            Union[PlatformTracks, types.Error]: An object containing search
                results, or an Error object if the query is empty or the
                search fails.
        """
        if not self.query:
            return types.Error(code=400, message="No search query provided")

        # If query is a valid URL, get info directly
        if self.is_valid():
            return await self.get_info()

        response = await self._make_api_request("search", {"query": self.query})
        return self._parse_tracks_response(response) or types.Error(
            code=404, message="No results found for search query"
        )

    async def get_track(self) -> TrackInfo | types.Error:
        """Retrieves detailed information for a single track.

        Returns:
            Union[TrackInfo, types.Error]: An object with detailed track
                metadata, or an Error object if the track cannot be found.
        """
        if not self.query:
            return types.Error(code=400, message="No track identifier provided")

        response = await self._make_api_request("track", {"url": self.query})
        if not response:
            return types.Error(code=404, message="Track not found")
        try:
            return TrackInfo.model_validate(response)
        except ValueError:
            return types.Error(code=502, message="Invalid track data returned by API")

    async def download_track(
        self, track: TrackInfo, video: bool = False
    ) -> Path | types.Error:
        """Downloads a track to local storage.

        This method handles the download process for a given track. It can
        use platform-specific downloaders (e.g., for Spotify) or a standard
        downloader for direct URLs.

        Args:
            track (TrackInfo): An object containing the track's metadata and
                download details.
            video (bool): Whether to download the video version of the track,
                if available. Defaults to False.

        Returns:
            Union[Path, types.Error]: The path to the downloaded file, or an
                Error object if the download fails.
        """
        if not track:
            return types.Error(code=400, message="Invalid track information provided")

        # Handle platform-specific download methods
        if track.platform.lower() == "spotify" and track.key:
            spotify_result = await SpotifyDownload(track).process()
            if isinstance(spotify_result, types.Error):
                LOGGER.error(f"Spotify download failed: {spotify_result.message}")
            return spotify_result

        # if track.platform.lower() == "youtube":
        #     return await YouTubeData().download_track(track, video)

        if not track.cdnurl:
            error_msg = f"No download URL available for track: {track.id}"
            LOGGER.error(error_msg)
            return types.Error(code=400, message=error_msg)

        # Standard download handling
        download_path = config.DOWNLOADS_DIR / f"{track.id}.mp3"
        download_result = await self.client.download_file(track.cdnurl, download_path)

        if not download_result.success or download_result.file_path is None:
            LOGGER.warning(
                f"Download failed for track {track.id}: {download_result.error}"
            )
            return types.Error(
                code=500,
                message=f"Download failed: {download_result.error or track.id}",
            )

        return download_result.file_path

    @staticmethod
    def _parse_tracks_response(
        response_data: dict[str, Any] | None,
    ) -> PlatformTracks | types.Error:
        """Parses and validates the API response for track data.

        This method processes the raw dictionary from an API response,
        validates its structure, and converts the track data into a
        `PlatformTracks` object.

        Args:
            response_data (Optional[dict]): The raw data from the API response.

        Returns:
            Union[PlatformTracks, types.Error]: A `PlatformTracks` object
                containing the parsed track data, or an `Error` object if the
                response is invalid or cannot be parsed.
        """
        if not response_data or "results" not in response_data:
            return types.Error(code=404, message="Invalid API response format")

        try:
            tracks = [
                MusicTrack(**track_data)
                for track_data in response_data["results"]
                if isinstance(track_data, dict)
            ]
            return (
                PlatformTracks(results=tracks)
                if tracks
                else types.Error(code=404, message="No valid tracks found")
            )
        except Exception as parse_error:
            LOGGER.error(f"Failed to parse tracks: {parse_error}")
            return types.Error(code=500, message="Failed to process track data")
