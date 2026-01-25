import json
import requests

from flask import Flask, render_template, redirect, url_for, jsonify, session, request
from app.helper import recommendations, create_playlist, lastfm_profile
import time
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Session configuration for HTTPS
app.config['SESSION_COOKIE_SECURE'] = app.config.get('REDIRECT_URL', '').startswith('https')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


def refresh_token_if_needed():
    """
    Check if the access token is expired and refresh it if needed.
    Returns the valid access_token or None if refresh failed.
    """
    sess_access_token = session.get("access_token")
    sess_refresh_token = session.get('refresh_token')
    sess_token_create_time = session.get('token_create')

    if not sess_access_token or not sess_refresh_token or not sess_token_create_time:
        return None

    # Check if token is expired (older than ~58 minutes)
    if (time.time() - sess_token_create_time) > 3500:
        token_url = "https://accounts.spotify.com/api/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"grant_type": "refresh_token", "refresh_token": sess_refresh_token}

        resp = requests.post(
            token_url,
            headers=headers,
            data=payload,
            auth=requests.auth.HTTPBasicAuth(
                app.config['SPOTIFY_CLIENT_ID'],
                app.config['SPOTIFY_CLIENT_SECRET']
            )
        )

        if 200 <= resp.status_code <= 299:
            parsed_resp = resp.json()
            session['access_token'] = parsed_resp['access_token']
            session['token_create'] = time.time()  # Update the token creation time
            return parsed_resp['access_token']
        else:
            return None

    return sess_access_token

#app routes
@app.route('/', methods=['GET'])
def landing():
    return render_template('landing.html')

@app.route('/generator', methods=['GET'])
def index():
    url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={app.config['SPOTIFY_CLIENT_ID']}&scope={app.config['SCOPE']}&redirect_uri={app.config['REDIRECT_URL']}"
    if 'access_token' not in session or 'refresh_token' not in session or 'token_create' not in session:
        #pop everything from session - incase one is missing 
        session.pop('access_token', None)
        session.pop('refresh_token', None)
        session.pop('token_create', None)
        session.pop('spotify_username', None)
        #redirect directly to spotify for oauth2 login 
        
        return redirect(url)
    
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return redirect(url)

    return render_template("index.html")

@app.route("/get-recommended-playlist", methods=["POST"])
def get_rec_playlist():
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    # Get json data from request
    data = request.get_json()

    # Fetch recommended tracks using Last.fm + Spotify search
    tracks = recommendations.gen_recommendations(data, sess_access_token, None)
    uris = [i['uri'] for i in tracks]
    resp_dict = {
        "songs": tracks,
        "uris": json.dumps(uris)
    }
    return jsonify(resp_dict) 

@app.route('/save-private-playlist', methods=['POST'])
def create_private_playlist():
    sess_username = session.get('spotify_username')

    if not sess_username:
        return jsonify({"error": "Not authenticated"}), 403

    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    # Get json data from request
    data = request.get_json()

    status = create_playlist.create_playlist(sess_username, sess_access_token, data)

    if not status:
        return jsonify({"error": "Error creating playlist"}), 400
    else:
        return jsonify({"success": True}), 200

@app.route('/spotify-oauth2callback', methods=['GET'])
def spotify_oauth2callback():
    code = request.args.get('code', None)

    if not code:
        return redirect(url_for('login')) 

    #get the access token and refresh token for this user 
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type":"authorization_code",
        "code":code,
        "redirect_uri":app.config['REDIRECT_URL']
    }
    resp = requests.post(url, headers=headers, data=payload, auth=requests.auth.HTTPBasicAuth(app.config['SPOTIFY_CLIENT_ID'], app.config['SPOTIFY_CLIENT_SECRET']))
    if 200 <= resp.status_code <= 299:
        parsed_resp = resp.json()
        #save the access and refresh tokens to session
        session['token_create'] = time.time()
        session['access_token'] = parsed_resp['access_token']
        session['refresh_token'] = parsed_resp['refresh_token'] 
         
        #get the user id to be used in playlist creation 
        profile_endpoint = "https://api.spotify.com/v1/me"
        headers = {"Authorization": f"Bearer {parsed_resp['access_token']}"}
        resp = requests.get(profile_endpoint, headers=headers) 
        json_resp = resp.json()
        session['spotify_username'] = json_resp['id']
        session.permanent = True

        return redirect(url_for('index'))
         
    else:
        return "Error during authentication", 200

@app.route('/profile')
def music_profile():
    """
    Analyze user's top tracks and create a taste profile using Last.fm tags.
    """
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return redirect(url_for('index'))

    # Get user's top tracks from Spotify
    time_range = request.args.get('time_range', 'medium_term')
    top_tracks = lastfm_profile.get_user_top_tracks(sess_access_token, limit=30, time_range=time_range)

    if not top_tracks:
        return "Could not fetch your top tracks", 400

    # Analyze tracks with Last.fm tags
    profile = lastfm_profile.analyze_tracks_profile(top_tracks)

    # Store profile in session for playlist generation
    session['taste_profile'] = {
        'scores': profile['scores'],
        'top_tags': profile['top_tags'][:10],
        'genres': profile['genres']
    }

    return render_template("profile.html",
                          profile=profile,
                          time_range=time_range)


@app.route('/api/profile', methods=['GET'])
def get_profile_api():
    """
    API endpoint to get user's taste profile as JSON.
    """
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    time_range = request.args.get('time_range', 'medium_term')
    top_tracks = lastfm_profile.get_user_top_tracks(sess_access_token, limit=30, time_range=time_range)

    if not top_tracks:
        return jsonify({"error": "Could not fetch top tracks"}), 400

    profile = lastfm_profile.analyze_tracks_profile(top_tracks)

    return jsonify({
        'scores': profile['scores'],
        'top_tags': profile['top_tags'][:15],
        'genres': profile['genres'],
        'track_count': profile['track_count']
    })


@app.route('/generate-from-profile', methods=['POST'])
def generate_from_profile():
    """
    Generate playlist recommendations based on user's taste profile.
    """
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    data = request.get_json()
    track_count = int(data.get('track-count', 15))

    # Get stored profile or create new one
    taste_profile = session.get('taste_profile')
    if not taste_profile:
        top_tracks = lastfm_profile.get_user_top_tracks(sess_access_token, limit=30)
        if top_tracks:
            profile = lastfm_profile.analyze_tracks_profile(top_tracks)
            taste_profile = {
                'scores': profile['scores'],
                'top_tags': profile['top_tags'][:10],
                'genres': profile['genres']
            }

    if not taste_profile:
        return jsonify({"error": "Could not create taste profile"}), 400

    # Generate tracks based on profile
    tracks = lastfm_profile.get_similar_tracks_by_profile(
        {'top_tags': taste_profile['top_tags'], 'scores': taste_profile['scores']},
        sess_access_token,
        limit=track_count
    )

    uris = [t['uri'] for t in tracks if t]
    return jsonify({
        "songs": tracks,
        "uris": json.dumps(uris),
        "profile_tags": taste_profile['top_tags'][:5]
    })


@app.route('/analyzer')
def playlist_analyzer():
    """Redirect old analyzer route to new profile page."""
    return redirect(url_for('music_profile'))


@app.route('/api/playlists', methods=['GET'])
def get_user_playlists():
    """
    Get all playlists of the current user.
    """
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    playlists = lastfm_profile.get_user_playlists(sess_access_token, limit=50)

    # Return simplified playlist data
    playlist_data = []
    for pl in playlists:
        playlist_data.append({
            'id': pl.get('id'),
            'name': pl.get('name'),
            'tracks_total': pl.get('tracks', {}).get('total', 0),
            'image': pl.get('images', [{}])[0].get('url') if pl.get('images') else None
        })

    return jsonify({"playlists": playlist_data})


@app.route('/api/playlist/<playlist_id>/analyze', methods=['GET'])
def analyze_playlist(playlist_id):
    """
    Analyze a specific playlist and return its mood profile.
    """
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    # Get tracks from playlist
    tracks = lastfm_profile.get_playlist_tracks(sess_access_token, playlist_id, limit=30)

    if not tracks:
        return jsonify({"error": "Could not fetch playlist tracks"}), 400

    # Analyze tracks
    profile = lastfm_profile.analyze_tracks_profile(tracks)

    # Store in session for later use
    session['playlist_profile'] = {
        'playlist_id': playlist_id,
        'scores': profile['scores'],
        'top_tags': profile['top_tags'][:10],
        'genres': profile['genres']
    }

    return jsonify({
        'scores': profile['scores'],
        'top_tags': profile['top_tags'][:15],
        'genres': profile['genres'],
        'track_count': profile['track_count']
    })


@app.route('/generate-from-playlist', methods=['POST'])
def generate_from_playlist():
    """
    Generate a new playlist based on:
    - Mood profile from selected playlist
    - Seed artist
    - Variety and Discovery settings
    """
    # Refresh token if needed
    sess_access_token = refresh_token_if_needed()
    if not sess_access_token:
        return jsonify({"error": "Token expired, please re-login"}), 401

    data = request.get_json()
    playlist_id = data.get('playlist_id')
    seed_artist = data.get('seed_artist', '').strip()
    variety = int(data.get('variety', 5))
    discovery = int(data.get('discovery', 5))
    track_count = int(data.get('track_count', 15))

    # Get or create profile from playlist
    playlist_profile = session.get('playlist_profile')

    # If no profile or different playlist, analyze it
    if not playlist_profile or playlist_profile.get('playlist_id') != playlist_id:
        if playlist_id:
            tracks = lastfm_profile.get_playlist_tracks(sess_access_token, playlist_id, limit=30)
            if tracks:
                profile = lastfm_profile.analyze_tracks_profile(tracks)
                playlist_profile = {
                    'playlist_id': playlist_id,
                    'scores': profile['scores'],
                    'top_tags': profile['top_tags'][:10],
                    'genres': profile['genres']
                }
                session['playlist_profile'] = playlist_profile

    if not playlist_profile:
        return jsonify({"error": "No playlist profile available"}), 400

    # Generate tracks
    tracks = lastfm_profile.generate_playlist_from_profile_and_artist(
        playlist_profile,
        seed_artist,
        sess_access_token,
        variety=variety,
        discovery=discovery,
        limit=track_count
    )

    uris = [t['uri'] for t in tracks if t]
    return jsonify({
        "songs": tracks,
        "uris": json.dumps(uris),
        "profile_tags": playlist_profile['top_tags'][:5],
        "seed_artist": seed_artist
    })
