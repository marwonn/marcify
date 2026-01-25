# Marcify - Playlist Generator

![Python3](https://img.shields.io/badge/Python-3-brightgreen)
![Flask](https://img.shields.io/badge/Flask-2.2.5-red)
![Docker](https://img.shields.io/badge/Docker-supported-blue)
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

## Deployment

### Option 1: Docker Compose (Recommended)

The easiest way to run Marcify on your own server.

#### Prerequisites

- Docker and Docker Compose installed
- Spotify Developer account
- Last.fm API key

#### Step 1: Get API Credentials

**Spotify:**
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Add redirect URI: `http://YOUR-SERVER:5000/spotify-oauth2callback`
4. In **User Management**, add your Spotify email
5. Copy **Client ID** and **Client Secret**

**Last.fm:**
1. Go to [Last.fm API](https://www.last.fm/api/account/create)
2. Create an API account
3. Copy your **API Key**

#### Step 2: Configure Environment

```bash
# Clone the repository
git clone https://github.com/marwonn/marcify.git
cd marcify

# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Fill in your `.env` file:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URL=http://your-server:5000/spotify-oauth2callback
SECRET_KEY=any_random_string_here
LASTFM_API_KEY=your_lastfm_api_key
USERNAME=your_spotify_username
```

#### Step 3: Start the Application

```bash
docker compose up -d
```

The app is now running at `http://your-server:5000`

#### Useful Docker Commands

```bash
# View logs
docker compose logs -f

# Stop the application
docker compose down

# Rebuild after updates
docker compose up -d --build

# Restart
docker compose restart
```

---

### Option 2: Deploy on Render

For a free cloud deployment without managing your own server.

1. Fork this repository to your GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Web Service**
4. Connect your GitHub and select the forked repo
5. Configure:

   | Setting | Value |
   |---------|-------|
   | **Name** | `your-app-name` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn wsgi:app` |

6. Add environment variables (same as above, but with Render URL):
   ```
   REDIRECT_URL=https://your-app-name.onrender.com/spotify-oauth2callback
   ```

7. Click **Deploy**

---

### Option 3: Run Locally (Development)

```bash
# Clone and enter directory
git clone https://github.com/marwonn/marcify.git
cd marcify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment file
cp .env.example .env
nano .env

# Run the app
flask run
```

App runs at `http://localhost:5000`

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SPOTIFY_CLIENT_ID` | From Spotify Developer Dashboard | `abc123...` |
| `SPOTIFY_CLIENT_SECRET` | From Spotify Developer Dashboard | `xyz789...` |
| `REDIRECT_URL` | OAuth callback URL (must match Spotify app settings) | `http://localhost:5000/spotify-oauth2callback` |
| `SECRET_KEY` | Random string for Flask sessions | `mysupersecretkey` |
| `LASTFM_API_KEY` | From Last.fm API | `def456...` |
| `USERNAME` | Your Spotify username | `myspotifyuser` |

---

## Playlist Settings

| Setting | Description |
|---------|-------------|
| **Seed Artist** | The artist to base recommendations on |
| **Variety** | How many different artists to explore (1-10) |
| **Discovery** | Balance between seed artist and new artists (1-10) |
| **Track Count** | Number of songs in the playlist (1-20) |
| **Fallback Genre** | Used when the seed artist can't be found |

---

## Project Structure

```
marcify/
├── app/
│   ├── helper/
│   │   ├── recommendations.py  # Last.fm + Spotify search logic
│   │   ├── create_playlist.py  # Spotify playlist creation
│   │   └── ...
│   ├── static/                 # CSS, JavaScript
│   ├── templates/              # HTML templates
│   ├── config.py               # Environment configuration
│   └── main.py                 # Flask routes
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── wsgi.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Error during authentication" | Redirect URL must match exactly in Spotify settings and `.env` |
| No recommendations found | Check that `LASTFM_API_KEY` is set correctly |
| 403 Forbidden from Spotify | Add your email in Spotify Dashboard → User Management |
| Container won't start | Check logs with `docker compose logs` |
| Token expired | App auto-refreshes tokens; try logging in again if issues persist |

---

## Links

- [Spotify Developer Documentation](https://developer.spotify.com/documentation/web-api)
- [Last.fm API Documentation](https://www.last.fm/api)

---

## License

Published under the GNU General Public License v3.0. See `LICENSE` for details.
