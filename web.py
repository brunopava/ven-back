import asyncio

from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel  # pylint: disable=E0611
from uvicorn import Config, Server

from spotdl.download.downloader import Downloader
from spotdl.types.song import Song
from spotdl.utils.query import parse_query
from spotdl.utils.search import get_search_results
from spotdl.utils.spotify import SpotifyClient, SpotifyError


class App:
    server: Any
    downloader: Downloader
    settings: Dict[str, Any]
    loop: asyncio.AbstractEventLoop


class SongModel(BaseModel):
    """
    A song object used for types and validation.
    We can't use the Song class directly because FastAPI doesn't support dataclasses.
    """

    name: str
    artists: List[str]
    artist: str
    album_name: str
    album_artist: str
    genres: List[str]
    disc_number: int
    disc_count: int
    copyright: str
    duration: int
    year: int
    date: str
    track_number: int
    tracks_count: int
    isrc: str
    song_id: str
    cover_url: str
    explicit: bool
    publisher: str
    url: str
    download_url: Optional[str] = None


class SettingsModel(BaseModel):
    """
    A settings object used for types and validation.
    """

    verbose: Optional[bool]
    cache_path: Optional[str]
    audio_provider: Optional[str]
    lyrics_provider: Optional[str]
    ffmpeg: Optional[str]
    variable_bitrate: Optional[int]
    constant_bitrate: Optional[int]
    ffmpeg_args: Optional[List[str]]
    format: Optional[str]
    save_file: Optional[str]
    m3u: Optional[str]
    output: Optional[str]
    overwrite: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    user_auth: Optional[bool]
    threads: Optional[int]
    browsers: Optional[List[str]]
    progress_handler: Optional[str]


# app = App()
# app.server = FastAPI()
# app.settings = SettingsModel()

app = FastAPI()

@app.get("/api/song/search")
def song_from_search(query: str) -> Song:
    """
    Search for a song on spotify using search query.
    And return the first result as a Song object.
    """

    return Song.from_search_term(query)


@app.get("/api/song/url")
def song_from_url(url: str) -> Song:
    """
    Search for a song on spotify using url.
    And return the first result as a Song object.
    """

    return Song.from_url(url)


@app.post("/api/songs/query")
def query_search(query: List[str]) -> List[Song]:
    """
    Parse query and return list of Song objects.
    """

    return parse_query(query)


@app.get("/api/songs/search")
def search_search(query: str) -> List[Song]:
    """
    Parse search term and return list of Song objects.
    """

    return get_search_results(query)


@app.post("/api/downloader/change_output")
def change_output(output: str) -> bool:
    """
    Change output folder
    """

    app.downloader.output = output

    return True


@app.post("/api/download/search")
async def download_search(
    query: str, return_file: bool = False
) -> Union[Tuple[Song, Optional[Path]], FileResponse]:
    """
    Search for song and download the first result.
    """

    song, path = await app.downloader.pool_download(Song.from_search_term(query))

    if return_file is True:
        if path is None:
            raise ValueError("No file found")

        return FileResponse(path)

    return song, path


@app.post("/api/download/objects")
async def download_objects(
    song: SongModel, return_file: bool = False
) -> Union[Tuple[Song, Optional[Path]], FileResponse]:
    """
    Download songs using Song objects.
    """

    song_obj, path = await app.downloader.pool_download(Song(**song.dict()))

    if return_file is True:
        if path is None:
            raise ValueError("No file found")

        return FileResponse(path)

    return song_obj, path


@app.get("/api/settings")
def get_settings() -> SettingsModel:
    """
    Return the settings object.
    """

    return SettingsModel(**app.settings)


@app.post("/api/settings/update")
def change_settings(settings: SettingsModel) -> bool:
    """
    Change downloader settings by reinitializing the downloader.
    """

    # Create shallow copy of settings
    settings_cpy = app.settings.copy()

    # Update settings with new settings that are not None
    settings_cpy.update({k: v for k, v in settings.dict().items() if v is not None})

    # Re-initialize downloader
    app.downloader = Downloader(
        audio_provider=settings_cpy["audio_provider"],
        lyrics_provider=settings_cpy["lyrics_provider"],
        ffmpeg=settings_cpy["ffmpeg"],
        variable_bitrate=settings_cpy["variable_bitrate"],
        constant_bitrate=settings_cpy["constant_bitrate"],
        ffmpeg_args=settings_cpy["ffmpeg_args"],
        output_format=settings_cpy["format"],
        save_file=settings_cpy["save_file"],
        threads=settings_cpy["threads"],
        output=settings_cpy["output"],
        overwrite=settings_cpy["overwrite"],
        m3u_file=settings_cpy["m3u"],
        progress_handler=None,
        # loop=app.loop,
    )

    return True


# def web(settings: Dict[str, Any]):
#     """
#     Run the web server.
#     """

#     loop = asyncio.new_event_loop()
#     app.settings = settings
#     app.loop = loop

#     SpotifyClient.init(
#         client_id=settings["client_id"],
#         client_secret=settings["client_secret"],
#         user_auth=settings["user_auth"],
#         cache_path=settings["cache_path"],
#         no_cache=settings["no_cache"],
#     )

#     app.downloader = Downloader(
#         audio_provider=settings["audio_provider"],
#         lyrics_provider=settings["lyrics_provider"],
#         ffmpeg=settings["ffmpeg"],
#         variable_bitrate=settings["variable_bitrate"],
#         constant_bitrate=settings["constant_bitrate"],
#         ffmpeg_args=settings["ffmpeg_args"],
#         output_format=settings["format"],
#         save_file=settings["save_file"],
#         threads=settings["threads"],
#         output=settings["output"],
#         overwrite=settings["overwrite"],
#         # m3u_file=settings["m3u"],
#         # progress_handler=None,
#         # loop=loop,
#     )

#     config = Config(app=app.server, port=8800, workers=1, loop=loop)  # type: ignore

#     server = Server(config)

#     loop.run_until_complete(server.serve())

#     if app.downloader.progress_handler:
#         app.downloader.progress_handler.close()

# tempsettings = {
#     'verbose': False,
#     'cache_path': '.',
#     'audio_provider': "youtube-music",
#     'lyrics_provider': "musixmatch",
#     'ffmpeg': "ffmpeg",
#     'variable_bitrate': None,
#     'constant_bitrate': None,
#     'ffmpeg_args': None,
#     'format': "mp3",
#     'save_file': None,
#     'm3u': None,
#     'output': ".",
#     'overwrite': "overwrite",
#     'client_id': '7375acea79274eb2b60280141f60c1c0',
#     'client_secret': '8eb64e22379e45a5ac4e064ed7f1c6ee',
#     'user_auth': False,
#     'threads': 1,
#     'browsers': Optional[List[str]],
#     'progress_handler': None,
#     'no_cache': None,
# }

# web(tempsettings)