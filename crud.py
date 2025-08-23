from sqlalchemy.orm import Session

import models
import schemas

def get_channel_by_key(db: Session, key: str):
    return db.query(models.Channel).filter(models.Channel.key == key).first()

def get_channels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Channel).offset(skip).limit(limit).all()

def create_channel(db: Session, channel: schemas.ChannelCreate):
    db_channel = models.Channel(**channel.model_dump())
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return schemas.Channel.model_validate(db_channel)

def delete_channel(db: Session, key: str):
    db_channel = get_channel_by_key(db, key)
    if db_channel:
        db.delete(db_channel)
        db.commit()
    return db_channel

def create_playlist(db: Session, playlist: schemas.PlaylistCreate):
    db_playlist = models.Playlist(title=playlist.title, key=playlist.key, thumbnail=playlist.thumbnail)
    
    for item in playlist.items:
        db_playlist.items.append(models.PlaylistItem(title=item.title, key=item.key, thumbnail=item.thumbnail, playlist_id=item.playlist_id))
    
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    
    from schemas import PlaylistRead
    return PlaylistRead.model_validate(db_playlist)

def get_playlists(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Playlist).offset(skip).limit(limit).all()

def get_playlists_by_key(db: Session, key: str):
    return db.query(models.Playlist).filter(models.Playlist.key == key).first()

def get_playlist_items(db: Session, playlist_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.PlaylistItem).filter(models.PlaylistItem.playlist_id == playlist_id).offset(skip).limit(limit).all()