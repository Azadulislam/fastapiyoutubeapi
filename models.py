from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    thumbnail = Column(String)

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    thumbnail = Column(String)
    items = relationship("PlaylistItem", back_populates="playlist", cascade="all, delete-orphan")

class PlaylistItem(Base):
    __tablename__ = "playlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    thumbnail = Column(String, nullable=False)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"))
    playlist = relationship("Playlist", back_populates="items")
