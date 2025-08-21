from sqlalchemy import Column, Integer, String
from database import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    profileImage = Column(String)

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    profileImage = Column(String)
