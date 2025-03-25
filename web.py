import asyncio

from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import FileResponse

from pydantic import BaseModel  # pylint: disable=E0611
from uvicorn import Config, Server

from spotdl.download.downloader import Downloader
from spotdl.types.song import Song
from spotdl.utils.search import get_search_results
from spotdl.utils.spotify import SpotifyClient, SpotifyError

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
    copyright_text: str
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

settings = {
    'verbose': False,
    'cache_path': '.',
    'audio_provider': "youtube-music",
    'lyrics_provider': "musixmatch",
    'ffmpeg': "ffmpeg",
    'variable_bitrate': None,
    'constant_bitrate': None,
    'ffmpeg_args': None,
    'format': "mp3",
    'save_file': None,
    'm3u': None,
    'output': ".",
    'overwrite': "overwrite",
    'client_id': '7375acea79274eb2b60280141f60c1c0',
    'client_secret': '8eb64e22379e45a5ac4e064ed7f1c6ee',
    'user_auth': False,
    'threads': 1,
    'browsers': Optional[List[str]],
    'progress_handler': None,
    'no_cache': None,
}

loop = asyncio.new_event_loop()

SpotifyClient.init(
    client_id=settings["client_id"],
    client_secret=settings["client_secret"],
    user_auth=settings["user_auth"],
    cache_path=settings["cache_path"],
    no_cache=settings["no_cache"],
)

downloader = Downloader(
    settings=settings,
    loop=loop
)

if downloader.progress_handler:
    downloader.progress_handler.close()

app = FastAPI()

@app.get("/api/song/search")
async def song_from_search(query: str) -> Song:
    """
    Search for a song on spotify using search query.
    And return the first result as a Song object.
    """
    song = await Song.from_search_term(query)
    return song

@app.get("/api/song/url")
def song_from_url(url: str) -> Song:
    """
    Search for a song on spotify using url.
    And return the first result as a Song object.
    """

    return Song.from_url(url)

@app.get("/api/songs/search")
def search(query: str) -> List[Song]:
    """
    Parse search term and return list of Song objects.
    """

    return get_search_results(query)

@app.post("/api/download/objects")
# async def download_objects()-> Union[Tuple[Song, Optional[Path]]]:
async def download_objects(info : Request) -> FileResponse:
    """
    Download songs using Song objects.
    """

    # print("here")
    print(info)
    json = await info.json()
    print(json)

    loorp = asyncio.get_event_loop()
    return await loorp.run_in_executor(None, downloader.search_and_download, Song(**json))



# @app.post("/api/download/song")
# async def download_song(
#     query: str, return_file: bool = False
# ) -> Union[Tuple[Song, Optional[Path]]]:
#     """
#     Search for song and download the first result.
#     """
#     print(query)
#     song, path = await downloader.pool_download(Song.from_search_term(query))

#     # async with downloader.semaphore:
#     #     song, path =  await loop.run_in_executor(None, downloader.search_and_download, song)

#     # if return_file is True:
#     #     if path is None:
#     #         raise ValueError("No file found")

#     #     # return FileResponse(path)

#     # return song, path

#     # # print(downloader.loop)
#     # song_obj, path = await downloader.pool_download(Song(**json))
#     # song_obj, path = await downloader.search_and_download(Song(**json))

#     # if path is None:
#     #     raise ValueError("No file found")

#     # return FileResponse(path)

#     # return song_obj, path

#     return