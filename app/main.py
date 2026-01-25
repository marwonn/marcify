import json 
import pandas as pd
import requests 
import spotipy

from flask import Flask, render_template, redirect, url_for, jsonify, session, request
from app.helper import figures, recommendations, create_playlist, audio_features
from datetime import datetime 
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Session configuration for HTTPS
app.config['SESSION_COOKIE_SECURE'] = app.config.get('REDIRECT_URL', '').startswith('https')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
    
    sess_access_token, sess_refresh_token, sess_token_create_time = session.get("access_token", None) , session.get('refresh_token', None), session.get('token_create', None)
    if (datetime.utcnow() - sess_token_create_time).total_seconds() > 3500:
        token_url = "https://accounts.spotify.com/api/token"
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        payload = {"grant_type":"refresh_token","refresh_token":sess_refresh_token}
        resp = requests.post(token_url, headers=headers, data=payload, auth=requests.auth.HTTPBasicAuth(app.config['SPOTIFY_CLIENT_ID'], app.config['SPOTIFY_CLIENT_SECRET']))
        
        if 200 <= resp.status_code <= 299:
            parsed_resp = resp.json()
            session['access_token'] = parsed_resp['access_token']

        else:
            return redirect(url)

    
    return render_template("index.html")

@app.route("/get-recommended-playlist", methods=["POST"])
def get_rec_playlist():
    #if expired, refresh the token here 
    sess_access_token, sess_refresh_token, sess_token_create_time = session.get("access_token", None) , session.get('refresh_token', None), session.get('token_create', None)

    if not sess_access_token or not sess_refresh_token or not sess_token_create_time:
        return "error, missing token", 403

    if (datetime.utcnow() - sess_token_create_time).total_seconds() > 3500:
        return "error, expired token", 400

    #get json data from request
    data = request.get_json()

    #fetch recommended tracks using Last.fm + Spotify search
    tracks = recommendations.gen_recommendations(data, sess_access_token, None)
    uris = [i['uri'] for i in tracks] 
    resp_dict = {
        "songs":tracks,
        "uris": json.dumps(uris)
    }
    return jsonify(resp_dict) 

@app.route('/save-private-playlist', methods=['POST'])
def create_private_playlist():
    sess_access_token, sess_refresh_token, sess_token_create_time, sess_username = session.get("access_token", None) , session.get('refresh_token', None), session.get('token_create', None), session.get('spotify_username', None)

    if not sess_access_token or not sess_refresh_token or not sess_token_create_time or not sess_username:
        return "error, missing token", 403 

    if (datetime.utcnow() - sess_token_create_time).total_seconds() > 3500:
        return "error, expired token", 400

    #get json data from request 
    data = request.get_json()

    status = create_playlist.create_playlist(sess_username, sess_access_token, data)

    if not status:
        return "Error creating playlist", 400
    else:
        return "Success creating playlist",200

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
        session['token_create'] = datetime.utcnow()
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

@app.route('/analyzer')
def playlist_analyzer():
    #if expired, refresh the token here 
    sess_access_token, sess_refresh_token, sess_token_create_time, sess_username = session.get("access_token", None) , session.get('refresh_token', None), session.get('token_create', None), session.get('spotify_username')

    if not sess_access_token or not sess_refresh_token or not sess_token_create_time:
        return "error, missing token", 403

    if (datetime.utcnow() - sess_token_create_time).total_seconds() > 3500:
        return "error, expired token", 400
    
    sp = spotipy.Spotify(auth=sess_access_token) 
    
    most_loved_songs_list = audio_features.get_playlist_audio_features(sess_username, sess_access_token, sp)
    (df, track_name, artist_name, popularity, album_cover) = most_loved_songs_list

    data = pd.DataFrame(df)
    number_counter = [i+1 for i in range(len(popularity)+1)]
    table_data = zip(number_counter, track_name, artist_name, popularity, album_cover)

    #violin_plot = figures.make_figures(track_name, popularity)
    radar_chart = figures.radar_chart(data)

    return render_template("analyzer.html", table_data=table_data,
                                            radar_chart=radar_chart)
