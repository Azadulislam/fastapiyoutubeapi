from sqlalchemy.orm import Session

import models
import schemas

def get_channel_by_key(db: Session, key: str):
    return db.query(models.Channel).filter(models.Channel.key == key).first()

def get_channels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Channel).offset(skip).limit(limit).all()

def create_channel(db: Session, channel: schemas.ChannelCreate):
    db_channel = models.Channel(**channel.dict())
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return schemas.Channel.from_orm(db_channel)

def delete_channel(db: Session, key: str):
    db_channel = get_channel_by_key(db, key)
    if db_channel:
        db.delete(db_channel)
        db.commit()
    return db_channel
