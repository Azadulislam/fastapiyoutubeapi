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
    id: str
    title: str
    description: str
    thumbnail: str

class PlaylistInfo(BaseModel):
    id: str
    title: str
