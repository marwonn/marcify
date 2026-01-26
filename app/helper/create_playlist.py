import json
import requests

def create_playlist(username, token, data):
    """
    Create a new Spotify playlist and add tracks to it.

    Args:
        username: Spotify user ID
        token: Access token
        data: Dict containing 'uris' (list of track URIs) and optionally 'name'
    """
    # Extract URIs and name from data
    uris = data.get('uris', [])
    playlist_name = data.get('name', 'Music Generator')

    # Handle case where uris might be a JSON string
    if isinstance(uris, str):
        try:
            uris = json.loads(uris)
        except json.JSONDecodeError:
            return False

    if not uris:
        return False

    # Create new playlist
    endpoint_url = f"https://api.spotify.com/v1/users/{username}/playlists"
    request_body = json.dumps({
        "name": playlist_name,
        "description": "Created by Magic Music Generator",
        "public": False
    })
    response = requests.post(
        url=endpoint_url,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )

    if response.status_code < 200 or response.status_code >= 300:
        return False

    playlist_id = response.json().get('id')
    if not playlist_id:
        return False

    # Add tracks to playlist
    endpoint_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    request_body = json.dumps({"uris": uris})

    response = requests.post(
        url=endpoint_url,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )

    return 200 <= response.status_code <= 299