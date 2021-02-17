import requests

song_endpoint = 'https://api.spotify.com/v1/me/player/currently-playing'
playlist_endpoint = 'https://api.spotify.com/v1/playlists/'

def get_headers(user):
    return {
        "Authorization": f"Bearer {user.userprofile.access_token}"
    }

def get_playlist_data(user, playlist_id):
    headers = get_headers(user)

    playlist_data = requests.get(playlist_endpoint + playlist_id, headers=headers)

    return playlist_data.json()

def get_song_data(user):
    headers = get_headers(user)

    song_data = requests.get(song_endpoint, headers=headers)

    return song_data.json()