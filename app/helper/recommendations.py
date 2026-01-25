import requests
import random
from flask import current_app


def get_similar_artists_lastfm(artist_name, limit=10):
    """
    Get similar artists from Last.fm API.
    Returns list of artist names.
    """
    api_key = current_app.config.get('LASTFM_API_KEY')
    if not api_key:
        return []

    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getsimilar",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json",
        "limit": limit
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "similarartists" in data and "artist" in data["similarartists"]:
                return [artist["name"] for artist in data["similarartists"]["artist"]]
    except Exception:
        pass

    return []


def get_artist_top_tracks_lastfm(artist_name, limit=5):
    """
    Get top tracks for an artist from Last.fm API.
    Returns list of track names.
    """
    api_key = current_app.config.get('LASTFM_API_KEY')
    if not api_key:
        return []

    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.gettoptracks",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json",
        "limit": limit
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "toptracks" in data and "track" in data["toptracks"]:
                return [(track["name"], artist_name) for track in data["toptracks"]["track"]]
    except Exception:
        pass

    return []


def search_track_on_spotify(track_name, artist_name, token):
    """
    Search for a track on Spotify and return track info if found.
    """
    query = f'track:"{track_name}" artist:"{artist_name}"'
    url = f"https://api.spotify.com/v1/search"
    params = {
        "q": query,
        "type": "track",
        "limit": 1,
        "market": "DE"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["tracks"]["items"]:
                return data["tracks"]["items"][0]
    except Exception:
        pass

    return None


def search_artist_top_tracks_spotify(artist_name, token, limit=3):
    """
    Search for an artist on Spotify and get their top tracks.
    Fallback when Last.fm is not available.
    """
    # First, find the artist
    url = "https://api.spotify.com/v1/search"
    params = {
        "q": f'artist:"{artist_name}"',
        "type": "artist",
        "limit": 1,
        "market": "DE"
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
        if not data["artists"]["items"]:
            return []

        artist_id = data["artists"]["items"][0]["id"]

        # Get top tracks for this artist
        top_tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
        params = {"market": "DE"}
        response = requests.get(top_tracks_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            tracks_data = response.json()
            return tracks_data.get("tracks", [])[:limit]
    except Exception:
        pass

    return []


def search_by_genre_spotify(genre, token, limit=10):
    """
    Search for tracks by genre on Spotify.
    Fallback method when artist-based search yields few results.
    """
    url = "https://api.spotify.com/v1/search"
    params = {
        "q": f'genre:"{genre}"',
        "type": "track",
        "limit": limit,
        "market": "DE"
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["tracks"]["items"]
    except Exception:
        pass

    return []


def gen_recommendations(payload, token, seed_artist_id):
    """
    Generate track recommendations using Last.fm similar artists + Spotify search.

    Since Spotify's /recommendations endpoint is deprecated for new apps,
    we use Last.fm to find similar artists and then search for their tracks on Spotify.

    Slider meanings:
    - variety (formerly danceability): How many different artists to explore (1-10)
    - popularity (formerly valence): Prefer popular vs obscure tracks (1-10)
    - discovery (formerly energy): Mix of seed artist vs similar artists (1-10)
    """
    track_count = int(payload.get('track-count', 10))
    variety = int(payload.get('variety', payload.get('danceability', 5)))
    discovery = int(payload.get('discovery', payload.get('energy', 5)))
    seed_genre = payload.get('seed-genre', 'rock')
    seed_artist_name = payload.get('seed-artist', '').strip()

    if not seed_artist_name:
        seed_artist_name = "Rage Against The Machine"

    collected_tracks = []
    seen_uris = set()

    # Calculate how many artists to explore based on variety slider
    num_similar_artists = max(2, variety)

    # Calculate balance between seed artist and similar artists based on discovery slider
    # Low discovery = more seed artist tracks, high discovery = more similar artist tracks
    seed_artist_track_ratio = max(0.1, 1 - (discovery / 10))
    seed_artist_tracks_target = max(1, int(track_count * seed_artist_track_ratio))
    similar_artist_tracks_target = track_count - seed_artist_tracks_target

    # Get tracks from seed artist via Spotify
    seed_tracks = search_artist_top_tracks_spotify(seed_artist_name, token, limit=seed_artist_tracks_target + 3)
    for track in seed_tracks:
        if track and track.get('uri') not in seen_uris:
            collected_tracks.append(track)
            seen_uris.add(track['uri'])
            if len([t for t in collected_tracks if any(a['name'].lower() == seed_artist_name.lower() for a in t.get('artists', []))]) >= seed_artist_tracks_target:
                break

    # Get similar artists from Last.fm
    similar_artists = get_similar_artists_lastfm(seed_artist_name, limit=num_similar_artists)

    # If Last.fm didn't return results, try genre-based search as fallback
    if not similar_artists:
        genre_tracks = search_by_genre_spotify(seed_genre, token, limit=track_count * 2)
        random.shuffle(genre_tracks)
        for track in genre_tracks:
            if track.get('uri') not in seen_uris:
                collected_tracks.append(track)
                seen_uris.add(track['uri'])
                if len(collected_tracks) >= track_count:
                    break
    else:
        # Get tracks from similar artists
        tracks_per_artist = max(1, similar_artist_tracks_target // len(similar_artists)) + 1

        for artist in similar_artists:
            if len(collected_tracks) >= track_count:
                break

            # Try to get top tracks from Spotify for this artist
            artist_tracks = search_artist_top_tracks_spotify(artist, token, limit=tracks_per_artist)

            for track in artist_tracks:
                if track and track.get('uri') not in seen_uris:
                    collected_tracks.append(track)
                    seen_uris.add(track['uri'])
                    if len(collected_tracks) >= track_count:
                        break

    # If we still don't have enough tracks, fill with genre search
    if len(collected_tracks) < track_count:
        genre_tracks = search_by_genre_spotify(seed_genre, token, limit=track_count)
        for track in genre_tracks:
            if track.get('uri') not in seen_uris:
                collected_tracks.append(track)
                seen_uris.add(track['uri'])
                if len(collected_tracks) >= track_count:
                    break

    # Shuffle to mix seed artist and similar artist tracks
    random.shuffle(collected_tracks)

    return collected_tracks[:track_count]
