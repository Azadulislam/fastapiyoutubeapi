from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import requests
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import json

# cache setup
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as aioredis

import models
import schemas
import crud
from database import SessionLocal, engine
from config import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Connect to Redis asynchronously

class ResponseValidationErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            return JSONResponse(
                status_code=422,
                content={"detail": e.errors()}
            )

app.add_middleware(ResponseValidationErrorMiddleware)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/channels/{username}", response_model=list[schemas.ChannelInfo])
async def get_channels_by_username(username: str):
    repUrl = f"{settings.youtube_api_url}search?part=snippet&type=channel&q={username}&maxResults=10&key={settings.youtube_api_key}"
    response = requests.get(repUrl)
    if response.status_code != 200 or not response.json().get("items"):
        # try:
        #     error_detail = 'af' + response.json().get("error", {}).get("message", "Unknown error")
        # except Exception:
        error_detail = response.text

        raise HTTPException(
            status_code=response.status_code,
            detail=f"YouTube API error: {error_detail}"
        )
    
    channels = response.json()["items"]
    channel_list = []
    for channel in channels:
        snippet = channel["snippet"]
        channel_list.append(
            schemas.ChannelInfo(
                key=channel["id"]["channelId"],
                title=snippet["title"],
                profileImage=snippet["thumbnails"]["default"]["url"],
                url=f"https://www.youtube.com/channel/{channel['id']['channelId']}",
            )
        )
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    await redis.set('channels', json.dumps([c.dict() for c in channel_list]))
    return channel_list

@app.get("/", response_model=list[schemas.Channel])
def read_channels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    channels = crud.get_channels(db, skip=skip, limit=limit)
    return channels


@app.post("/channel", response_model=schemas.Channel)
async def create_channel(channelKey: schemas.ChannelCreate, db: Session = Depends(get_db)):
    
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    cached_channels = await redis.get('channels')
    db_channel = crud.get_channel_by_key(db, key=channelKey.key)
    if db_channel:
        await redis.delete("channels")
        raise HTTPException(status_code=400, detail="Channel already registered")
    channel_data = []
    if cached_channels:
        for channel in json.loads(cached_channels):
            if(channel["key"] == channelKey.key):
                channel_data = channel
                break
        
    if not channel_data:
        repUrl = f"{settings.youtube_api_url}channels?part=snippet&id={channelKey.key}&key={settings.youtube_api_key}"
        response = requests.get(repUrl)
        if response.status_code != 200 or not response.json().get("items"):
            raise HTTPException(status_code=404, detail="YouTube channel not found")
        channel_data = response.json()["items"][0]["snippet"]
        
        db_channel = crud.create_channel(
            db=db,
            channel=schemas.ChannelBase(
                key=channel_data["channelId"],
                title=channel_data["title"],
                profileImage=channel_data["thumbnails"]["default"]["url"],
                url=f"https://www.youtube.com/channel/{channel_data['channelId']}",
            )
        )
        await redis.delete("channels")
    else:
        db_channel = crud.create_channel(
            db=db,
            channel=schemas.ChannelBase(
                key=channel_data["key"],
                title=channel_data["title"],
                profileImage=channel_data["profileImage"],
                url=f"https://www.youtube.com/channel/{channel_data['key']}",
            )
        )     
    return db_channel

@app.delete("/channel/{key}", response_model=schemas.Channel)
def delete_channel_for_user(key: str, db: Session = Depends(get_db)):
    db_channel = crud.delete_channel(db, key=key)
    if db_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return db_channel

@app.get("/playlist/{channel_key}", response_model=list[schemas.PlaylistInfo])
async def get_playlist_by_channel(channel_key: str):
    # Find the playlist containing the video
    playlist_search_url = f"{settings.youtube_api_url}playlists?part=snippet&channelId={channel_key}&maxResults=20&key={settings.youtube_api_key}"
    playlist_response = requests.get(playlist_search_url)
    if playlist_response.status_code != 200 or not playlist_response.json().get("items"):
        raise HTTPException(status_code=404, detail="Playlist not found for this video")
    playlists = playlist_response.json()["items"]
    returned_playlists = []
    for playlist in playlists:
        playlist_id = playlist["id"]
        playlist_title = playlist["snippet"]["title"]
        returned_playlists.append(
            schemas.PlaylistInfo(
                key=playlist_id,
                title=playlist_title,
                description=playlist["snippet"]["description"],
                thumbnail=playlist["snippet"]["thumbnails"]["default"]["url"]
            )
        )

    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    await redis.set('playlists', json.dumps([c.dict() for c in returned_playlists]))
    return returned_playlists

@app.post("/save-playlist", response_model=list[schemas.PlaylistInfo])
async def save_playlist(playlist_keys: list[str], db: Session = Depends(get_db)):
    # Find the playlist containing the video

    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    playlist_data = await redis.get('playlists')
    playlists = []
    if not playlist_data:
        raise HTTPException(status_code=404, detail="No playlists found in Redis")

    try:
        playlists = json.loads(playlist_data)
        if not isinstance(playlists, list):
            raise ValueError("Invalid playlist data format in Redis")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse playlist data from Redis")\

    matching_playlists = [p for p in playlists if p.get("key") in playlist_keys]
    returned_playlists = []
    for playlist in matching_playlists:
        # Ensure required fields exist
        items = []
        playlist_id = playlist["key"]
        next_page_token = None

        while True:
            playlist_items_url = (
                f"{settings.youtube_api_url}playlistItems?part=snippet"
                f"&playlistId={playlist_id}&maxResults=50"
                f"&key={settings.youtube_api_key}"
                f"{f'&pageToken={next_page_token}' if next_page_token else ''}"
            )
            try:
                response = requests.get(playlist_items_url)
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Could not retrieve playlist items")
                data = response.json()
            except requests.RequestException as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch playlist items: {str(e)}")

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                if not all(key in snippet for key in ["resourceId", "title", "description", "thumbnails"]):
                    continue
                if "videoId" not in snippet["resourceId"] or "default" not in snippet["thumbnails"]:
                    continue
                items.append(
                    schemas.PlaylistItem(
                        key=snippet["resourceId"]["videoId"],
                        title=snippet["title"],
                        playlist_id=playlist_id,
                        description=snippet["description"],
                        thumbnail=snippet["thumbnails"]["default"]["url"],
                    )
                )

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
        # Create playlist in database
        playlist_info = schemas.PlaylistInfo(
            key=playlist['key'],
            title=playlist["title"],
            description=playlist["description"],
            thumbnail=playlist["thumbnail"],
            items=items
        )
        crud.create_playlist(db=db, playlist=playlist_info)
        returned_playlists.append(playlist_info)

    return returned_playlists

@app.get("/playlistitems/{playlist_key}", response_model=schemas.PlaylistInfo)
def get_playlist_items_by_playlist(playlist_key: str):
    # Get the items in the playlist
    playlist_items_url = f"{settings.youtube_api_url}playlistItems?part=snippet&playlistId={playlist_key}&maxResults=50&key={settings.youtube_api_key}"
    items_response = requests.get(playlist_items_url)
    if items_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Could not retrieve playlist items")

    playlist_items = []
    for item in items_response.json()["items"]:
        snippet = item["snippet"]
        playlist_items.append(
            schemas.PlaylistItem(
                key=snippet["resourceId"]["videoId"],
                title=snippet["title"],
                description=snippet["description"],
                thumbnail=snippet["thumbnails"]["default"]["url"],
            )
        )

    return schemas.PlaylistInfo(
        id=playlist_id,
        title=playlist_title,
        description=playlist_description,
        items=playlist_items,
    )
 

@app.post("/playlists", response_model=schemas.PlaylistRead)
def create_playlist_endpoint(playlist: schemas.PlaylistCreate, db: Session = Depends(get_db)):
    return create_playlist_with_items(db, playlist)