# Marcify - Playlist Generator

![Python3](https://img.shields.io/badge/Python-3-brightgreen)
![Flask](https://img.shields.io/badge/Flask-2.2.5-red)
![jQuery](https://img.shields.io/badge/jQuery-3.5.1-yellow)
![Bootstrap](https://img.shields.io/badge/Bootstrap-4.5.2-blue)
![License](https://img.shields.io/badge/License-GPL%20v3.0-lightgrey)

Generate personalized Spotify playlists based on your favorite artists. Enter a seed artist, adjust the settings, and create a playlist with similar music.

![screenshot](./screenshots/screenshot_1.png)

---

## How It Works

1. **Login** with your Spotify account
2. **Enter a seed artist** (e.g., "Radiohead", "Kendrick Lamar")
3. **Adjust the sliders** to customize your playlist
4. **Generate** recommendations and preview the tracks
5. **Save** the playlist directly to your Spotify account

### Technical Background

Since Spotify deprecated their `/recommendations` API endpoint in November 2024, this app uses an alternative approach:

- **Last.fm API** finds artists similar to your seed artist
- **Spotify Search API** fetches top tracks from those artists
- The results are combined into a personalized playlist

---

## Quick Start

### 1. Prerequisites

You need accounts on:
- [Spotify Developer](https://developer.spotify.com) (free)
- [Last.fm API](https://www.last.fm/api/account/create) (free)
- [Render](https://render.com) (free tier available)
- GitHub

### 2. Set Up Spotify App

1. Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Click **Create App**
3. Fill in the app details
4. In **Settings**, add a Redirect URI:
   ```
   https://YOUR-APP-NAME.onrender.com/spotify-oauth2callback
   ```
5. Go to **User Management** and add your Spotify email (required for testing)
6. Note your **Client ID** and **Client Secret**

### 3. Get Last.fm API Key

1. Go to [Last.fm API Account Creation](https://www.last.fm/api/account/create)
2. Fill in the form (application name, description)
3. Note your **API Key**

### 4. Deploy on Render

1. Fork this repository to your GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Web Service**
4. Connect your GitHub and select the forked repo
5. Configure the service:

   | Setting | Value |
   |---------|-------|
   | **Name** | `your-app-name` (must match the redirect URI) |
   | **Region** | Choose nearest to you |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn wsgi:app` |

6. Add **Environment Variables**:

   | Key | Value |
   |-----|-------|
   | `SPOTIFY_CLIENT_ID` | Your Spotify Client ID |
   | `SPOTIFY_CLIENT_SECRET` | Your Spotify Client Secret |
   | `REDIRECT_URL` | `https://your-app-name.onrender.com/spotify-oauth2callback` |
   | `SECRET_KEY` | Any random string (e.g., `mysecretkey123`) |
   | `LASTFM_API_KEY` | Your Last.fm API Key |
   | `USERNAME` | Your Spotify username |

7. Click **Deploy** and wait for the build to complete

---

## Playlist Settings Explained

| Setting | Description |
|---------|-------------|
| **Seed Artist** | The artist to base recommendations on. Similar artists will be found. |
| **Variety** | How many different artists to explore (1 = few, 10 = many) |
| **Discovery** | Balance between seed artist and new artists (1 = mostly seed artist, 10 = mostly new artists) |
| **Track Count** | Number of songs in the playlist (1-20) |
| **Fallback Genre** | Used when the seed artist can't be found |

---

## Running Locally

```bash
# Clone the repository
git clone https://github.com/your-username/marcify.git
cd marcify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create a .env file or export manually)
export SPOTIFY_CLIENT_ID=your_client_id
export SPOTIFY_CLIENT_SECRET=your_client_secret
export REDIRECT_URL=http://localhost:5000/spotify-oauth2callback
export SECRET_KEY=your_secret_key
export LASTFM_API_KEY=your_lastfm_key
export USERNAME=your_spotify_username

# Run the app
flask run
```

**Note:** For local development, add `http://localhost:5000/spotify-oauth2callback` to your Spotify app's redirect URIs.

---

## Project Structure

```
marcify/
├── app/
│   ├── helper/
│   │   ├── recommendations.py  # Last.fm + Spotify search logic
│   │   ├── create_playlist.py  # Spotify playlist creation
│   │   └── ...
│   ├── static/
│   │   ├── css/
│   │   └── js/main.js
│   ├── templates/
│   │   ├── index.html          # Main generator page
│   │   └── ...
│   ├── config.py               # Environment configuration
│   └── main.py                 # Flask routes
├── requirements.txt
├── wsgi.py
└── README.md
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Error during authentication" | Check that your Redirect URL matches exactly in Spotify and Render |
| No recommendations found | Make sure `LASTFM_API_KEY` is set correctly |
| 403 Forbidden | Add your Spotify email to User Management in the Spotify Developer Dashboard |
| Token expired | The app should auto-refresh; if not, try logging in again |

---

## Links

- [Spotify Developer Documentation](https://developer.spotify.com/documentation/web-api)
- [Last.fm API Documentation](https://www.last.fm/api)
- [Original Repository](https://github.com/marwonn/spotify-playlist-generator-analyzer)

---

## License

Published under the GNU General Public License v3.0. See `LICENSE` for details.
