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

## Quick Start with Docker

The fastest way to get Marcify running. No need to clone the repository.

### Step 1: Get API Credentials

**Spotify:**
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Add redirect URI: `http://localhost:5000/spotify-oauth2callback`
4. In **User Management**, add your Spotify email
5. Copy **Client ID** and **Client Secret**

**Last.fm:**
1. Go to [Last.fm API](https://www.last.fm/api/account/create)
2. Create an API account
3. Copy your **API Key**

### Step 2: Download and Configure

```bash
# Download the compose file
curl -O https://raw.githubusercontent.com/marwonn/marcify/master/docker-compose.ghcr.yml

# Edit and fill in your API credentials
nano docker-compose.ghcr.yml
```

Fill in your credentials in the `environment` section:

```yaml
environment:
  - SPOTIFY_CLIENT_ID=your_spotify_client_id
  - SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
  - REDIRECT_URL=http://localhost:5000/spotify-oauth2callback
  - SECRET_KEY=change_this_to_a_random_string
  - LASTFM_API_KEY=your_lastfm_api_key
  - USERNAME=your_spotify_username
```

### Step 3: Start

```bash
docker compose -f docker-compose.ghcr.yml up -d
```

Open http://localhost:5000 in your browser.

### Useful Commands

```bash
# View logs
docker compose -f docker-compose.ghcr.yml logs -f

# Stop
docker compose -f docker-compose.ghcr.yml down

# Update to latest version
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d
```

---

## Deployment on a Server

For server deployment, change the `REDIRECT_URL` to match your server:

```yaml
- REDIRECT_URL=http://your-server-ip:5000/spotify-oauth2callback
```

Or with a domain and reverse proxy (nginx/traefik):

```yaml
- REDIRECT_URL=https://marcify.yourdomain.com/spotify-oauth2callback
```

**Important:** Update the redirect URI in your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) to match.

---

## Alternative Deployment Options

### Build from Source

```bash
git clone https://github.com/marwonn/marcify.git
cd marcify
cp .env.example .env
nano .env  # Fill in your credentials
docker compose up -d
```

### Deploy on Render (Free Cloud Hosting)

1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Create a new **Web Service** and connect your fork
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn wsgi:app`
6. Add environment variables
7. Deploy

### Run without Docker (Development)

```bash
git clone https://github.com/marwonn/marcify.git
cd marcify
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
flask run
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SPOTIFY_CLIENT_ID` | From Spotify Developer Dashboard |
| `SPOTIFY_CLIENT_SECRET` | From Spotify Developer Dashboard |
| `REDIRECT_URL` | OAuth callback URL (must match Spotify app settings) |
| `SECRET_KEY` | Random string for Flask sessions |
| `LASTFM_API_KEY` | From Last.fm API |
| `USERNAME` | Your Spotify username |

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

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Error during authentication" | Redirect URL must match exactly in Spotify settings and compose file |
| No recommendations found | Check that `LASTFM_API_KEY` is set correctly |
| 403 Forbidden from Spotify | Add your email in Spotify Dashboard → User Management |
| Container won't start | Check logs with `docker compose -f docker-compose.ghcr.yml logs` |

---

## Links

- [Spotify Developer Documentation](https://developer.spotify.com/documentation/web-api)
- [Last.fm API Documentation](https://www.last.fm/api)

---

## License

Published under the GNU General Public License v3.0. See `LICENSE` for details.
