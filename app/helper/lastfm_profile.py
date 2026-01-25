import requests
from flask import current_app
from collections import Counter


# Tag categories for mood/energy profiling
TAG_CATEGORIES = {
    'energy': {
        'high': ['energetic', 'powerful', 'intense', 'aggressive', 'heavy', 'fast', 'upbeat', 'driving', 'hard'],
        'low': ['calm', 'chill', 'relaxing', 'mellow', 'soft', 'slow', 'ambient', 'peaceful', 'gentle']
    },
    'mood': {
        'high': ['happy', 'uplifting', 'cheerful', 'fun', 'feel good', 'joyful', 'optimistic', 'bright'],
        'low': ['sad', 'melancholic', 'dark', 'depressing', 'angry', 'aggressive', 'haunting', 'moody']
    },
    'danceability': {
        'high': ['dance', 'danceable', 'groovy', 'funky', 'rhythm', 'beat', 'club', 'party', 'disco'],
        'low': ['ballad', 'slow', 'ambient', 'atmospheric', 'experimental', 'noise']
    },
    'acousticness': {
        'high': ['acoustic', 'unplugged', 'folk', 'singer-songwriter', 'organic', 'live'],
        'low': ['electronic', 'synth', 'digital', 'produced', 'industrial', 'edm']
    }
}


def get_track_tags_lastfm(track_name, artist_name, limit=10):
    """
    Get tags for a track from Last.fm API.
    Returns list of tag names.
    """
    api_key = current_app.config.get('LASTFM_API_KEY')
    if not api_key:
        return []

    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "track.gettoptags",
        "track": track_name,
        "artist": artist_name,
        "api_key": api_key,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "toptags" in data and "tag" in data["toptags"]:
                tags = data["toptags"]["tag"]
                if isinstance(tags, list):
                    return [tag["name"].lower() for tag in tags[:limit]]
                elif isinstance(tags, dict):
                    return [tags["name"].lower()]
    except Exception:
        pass

    return []


def get_artist_tags_lastfm(artist_name, limit=10):
    """
    Get tags for an artist from Last.fm API.
    Fallback when track tags are not available.
    """
    api_key = current_app.config.get('LASTFM_API_KEY')
    if not api_key:
        return []

    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.gettoptags",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "toptags" in data and "tag" in data["toptags"]:
                tags = data["toptags"]["tag"]
                if isinstance(tags, list):
                    return [tag["name"].lower() for tag in tags[:limit]]
    except Exception:
        pass

    return []


def calculate_tag_scores(tags):
    """
    Calculate scores for each category based on tags.
    Returns dict with scores from 0.0 to 1.0 for each category.
    """
    scores = {}

    for category, keywords in TAG_CATEGORIES.items():
        high_count = sum(1 for tag in tags if any(kw in tag for kw in keywords['high']))
        low_count = sum(1 for tag in tags if any(kw in tag for kw in keywords['low']))

        total = high_count + low_count
        if total > 0:
            # Score from 0.0 (all low) to 1.0 (all high)
            scores[category] = high_count / total
        else:
            scores[category] = 0.5  # Neutral if no matching tags

    return scores


def get_user_top_tracks(token, limit=50, time_range='medium_term'):
    """
    Get user's top tracks from Spotify.
    time_range: short_term (4 weeks), medium_term (6 months), long_term (years)
    """
    url = f"https://api.spotify.com/v1/me/top/tracks"
    params = {
        "limit": limit,
        "time_range": time_range
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
    except Exception:
        pass

    return []


def analyze_tracks_profile(tracks):
    """
    Analyze a list of tracks and create a taste profile based on Last.fm tags.
    Returns profile dict with scores and top tags.
    """
    all_tags = []
    track_analyses = []

    for track in tracks:
        track_name = track.get('name', '')
        artists = track.get('artists', [])
        artist_name = artists[0]['name'] if artists else ''

        # Get tags for this track
        tags = get_track_tags_lastfm(track_name, artist_name)

        # Fallback to artist tags if track has no tags
        if not tags and artist_name:
            tags = get_artist_tags_lastfm(artist_name)

        all_tags.extend(tags)

        track_analyses.append({
            'name': track_name,
            'artist': artist_name,
            'tags': tags[:5],
            'scores': calculate_tag_scores(tags)
        })

    # Calculate overall profile
    tag_counts = Counter(all_tags)
    top_tags = tag_counts.most_common(20)

    # Average scores across all tracks
    avg_scores = {}
    for category in TAG_CATEGORIES.keys():
        scores = [t['scores'].get(category, 0.5) for t in track_analyses if t['scores']]
        avg_scores[category] = sum(scores) / len(scores) if scores else 0.5

    # Extract genre tags (common music genres)
    genre_keywords = ['rock', 'pop', 'hip hop', 'rap', 'electronic', 'jazz', 'classical',
                      'metal', 'punk', 'indie', 'alternative', 'r&b', 'soul', 'country',
                      'folk', 'blues', 'reggae', 'latin', 'dance', 'house', 'techno']
    genres = [tag for tag, count in top_tags if any(g in tag for g in genre_keywords)][:5]

    return {
        'scores': avg_scores,
        'top_tags': top_tags,
        'genres': genres,
        'track_count': len(tracks),
        'track_analyses': track_analyses
    }


def get_similar_tracks_by_profile(profile, token, limit=20):
    """
    Find tracks that match the user's taste profile using Last.fm similar artists
    and filtering by tags.
    """
    from app.helper.recommendations import get_similar_artists_lastfm, search_artist_top_tracks_spotify

    # Use top genres/tags to find seed artists
    collected_tracks = []
    seen_uris = set()

    # Get artists similar to the profile's top tags
    for tag, count in profile['top_tags'][:5]:
        # Search for artists by tag
        similar_artists = get_artists_by_tag(tag, limit=5)

        for artist in similar_artists:
            if len(collected_tracks) >= limit:
                break

            tracks = search_artist_top_tracks_spotify(artist, token, limit=3)
            for track in tracks:
                if track and track.get('uri') not in seen_uris:
                    collected_tracks.append(track)
                    seen_uris.add(track['uri'])

    return collected_tracks[:limit]


def get_artists_by_tag(tag, limit=10):
    """
    Get top artists for a tag from Last.fm.
    """
    api_key = current_app.config.get('LASTFM_API_KEY')
    if not api_key:
        return []

    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "tag.gettopartists",
        "tag": tag,
        "api_key": api_key,
        "format": "json",
        "limit": limit
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "topartists" in data and "artist" in data["topartists"]:
                return [artist["name"] for artist in data["topartists"]["artist"]]
    except Exception:
        pass

    return []
