"""
Music/Mood video extraction models
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from .base import BaseExtraction


class SongMetadata(BaseExtraction):
    """
    Song metadata extracted from a music video reel.
    
    Example:
        SongMetadata(
            category="music",
            title="Summer Vibes Playlist",
            description="Upbeat summer songs",
            song_title="Blinding Lights",
            artist="The Weeknd",
            genre="Pop",
            lyrics_snippet="I've been tryna call...",
            spotify_link="https://open.spotify.com/track/...",
            youtube_link="https://youtube.com/watch?v=...",
            mood="Energetic"
        )
    """
    category: Literal["music"] = "music"
    song_title: Optional[str] = Field(
        None, 
        description="Title of the song"
    )
    artist: Optional[str] = Field(
        None, 
        description="Artist or band name"
    )
    genre: Optional[str] = Field(
        None, 
        description="Music genre (e.g., 'Pop', 'Rock', 'Hip-Hop', 'Electronic')"
    )
    lyrics_snippet: Optional[str] = Field(
        None, 
        description="Snippet of lyrics from the song"
    )
    spotify_link: Optional[str] = Field(
        None, 
        description="Link to the song on Spotify"
    )
    youtube_link: Optional[str] = Field(
        None, 
        description="Link to the song on YouTube"
    )
    mood: Optional[str] = Field(
        None, 
        description="Mood or vibe of the song (e.g., 'Energetic', 'Relaxing', 'Melancholic')"
    )

