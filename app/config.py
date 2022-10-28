import os

class Config:
    """
    user credentials configuration 
    """
    USERNAME = os.getenv("USERNAME")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

    SCOPE = "playlist-modify-private%20playlist-read-private%20user-top-read"

    REDIRECT_URL = os.getenv("REDIRECT_URL")
    