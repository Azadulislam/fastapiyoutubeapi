from pydantic import BaseModel
from typing import Optional

class ChannelInfo(BaseModel):
    key: str
    title: Optional[str] = None
    description: Optional[str] = None
    profileImage: Optional[str] = None
    url: Optional[str] = None

class ChannelBase(BaseModel):
    key: str
    title: Optional[str] = None
    url: Optional[str] = None
    profileImage: Optional[str] = None

class ChannelCreate(ChannelBase):
    pass

class Channel(ChannelBase):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    profileImage: Optional[str] = None

    class Config:
        from_attributes = True

class ChannelDetails(BaseModel):
    key: str

class PlaylistItem(BaseModel):
    title: str
    key: str
    description: Optional[str] = None
    playlist_id: str
    thumbnail: str

class PlaylistInfo(BaseModel):
    title: str
    key: str
    description: Optional[str] = None
    thumbnail: str
    items: list[PlaylistItem] = []


class PlaylistKeys(BaseModel):
    keys: list[str]


class PlaylistItemCreate(BaseModel):
    key: str
    title: str
    playlist_id: int
    description: Optional[str] = None
    thumbnail: str

class PlaylistCreate(BaseModel):
    title: str
    key: str
    thumbnail: str
    items: list[PlaylistItemCreate]

class PlaylistItemRead(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}

class PlaylistRead(BaseModel):
    id: int
    title: str
    items: list[PlaylistItemRead] = []

    model_config = {"from_attributes": True}