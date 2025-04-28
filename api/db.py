from sqlalchemy import create_engine, Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    display_name = Column(String)
    refresh_token = Column(String)

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)

class Track(Base):
    __tablename__ = "tracks"
    id = Column(String, primary_key=True)
    playlist_id = Column(String, ForeignKey("playlists.id"))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    artist = Column(String)
    colour = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)

