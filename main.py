from flask import Flask, redirect, request, jsonify, session
import requests
import secrets
import string
import urllib.parse
from urllib.parse import urlparse, parse_qs 
from dotenv import load_dotenv
import os
import base64
import json



load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"

def token_urlsafe(length):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))

@app.route("/login")
def login():
    state = token_urlsafe(16)
    scope = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private"

    query_parameters = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "show_dialog": True
    }

    spotify_auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(query_parameters)
    return redirect(spotify_auth_url)

@app.route('/callback')
def callback():
    url = request.url
    parsed_url = urlparse(url)
    query_url = parse_qs(parsed_url.query)

    code = query_url.get("code", [None])[0]
    state = query_url.get("state", [None])[0]

    token_request = {
        "url": "https://accounts.spotify.com/api/token",
        "data": {

        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
        }
    }
    auth_credentials = client_id + ":" + client_secret
    auth_bytes = auth_credentials.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    headers = {

        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + auth_base64
    }
    response = requests.post(token_request['url'], data=token_request['data'], headers=headers)
    json_response = json.loads(response.content)

    session['access_token'] = json_response["access_token"]
    return redirect('/token')


@app.route('/token')
def show__token():
    token = session.get('access_token')
    return "Your access token is " + token

def get_user_saved_track():
    
    token = session.get('access_token')
    

    track_url = "https://api.spotify.com/v1/me/tracks"
    header = {"Authorization": "Bearer " + token}
    limit = 50
    offset = 0
    track_dictionary = {}
    
    while True:

        params = {
            "limit": limit,
            "offset": offset
        }
            
        response = requests.get(track_url, headers=header, params=params)

        data = response.json()


        for item in data['items']:
            track = item['track']
            track_id = track['id']
            track_name = track['name']

            track_dictionary[track_id] = track_name

        if data['next'] is None:
            break


        offset += limit

    return track_dictionary

@app.route('/json_dictionary')
def json_dictionary():
    track_dictionary = get_user_saved_track()

    return jsonify(track_dictionary)

def get_energy():
    token = session.get("access_token")
    audio_url = "https://api.spotify.com/v1/audio-features"
    header = {"Authorization": "Bearer " + token}
    
    track_dictionary = get_user_saved_track()
    track_ids = list(track_dictionary.keys())

    track_features = {}

    for i in range(0, len(track_ids), 100):
        track_id_chunk = track_ids[i:i+100]
        track_id_string = ",".join(track_id_chunk)

        response = requests.get(f"{audio_url}?ids={track_id_string}", headers=header)
        audio_features = response.json()

        for track in audio_features["audio_features"]:
            if track:
                track_id = track["id"]
                energy = track["energy"]
                valence = track["valence"]

                track_features[track_id] = {
                    "valence": valence,
                    "energy": energy
                }
                

    return track_features

def create_mood_dictionaries(track_features):

    dictionaries = {
        "low_energy_low_valence": {},
        "high_energy_high_valence": {},
        "low_energy_high_valence": {},
        "high_energy_low_valence": {},
    }

    for track_id, features in track_features.items():
        valence = features["valence"]
        energy = features["energy"]

        if valence <= 0.3 and energy <= 0.3:
            dictionaries["low_energy_low_valence"][track_id] = features
        elif valence >= 0.7 and energy >= 0.7:
            dictionaries["high_energy_high_valence"][track_id] = features
        elif valence >= 0.7 and energy <= 0.3:
            dictionaries["low_energy_high_valence"][track_id] = features
        elif valence <= 0.3 and energy >= 0.7:
            dictionaries["high_energy_low_valence"][track_id] = features

    return dictionaries

@app.route('/valence_dictionary')

def valence_dictionaryy():
    valence_dictionary = get_energy()

    return jsonify(valence_dictionary)


@app.route('/mixed_dictionary')

def mixed_dictionary():
    mixed_dictionary = get_energy()
    dictionaries = create_mood_dictionaries(mixed_dictionary)

    return jsonify(dictionaries)

def get_username():
    token = session.get("access_token")
    url = "https://api.spotify.com/v1/me"
    header = {"Authorization": "Bearer " + token}

    response = requests.get(url, headers=header)
    data = response.json()

    user_id = data['id']
    return user_id

def create_playlists(user_id, dictionaries):
    token = session.get("access_token")
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers =  {
        
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
            }
    
    playlist_data = {
        "Low energy, Low valence": dictionaries["low_energy_low_valence"],
        "Low energy, High valence": dictionaries["low_energy_high_valence"],
        "High energy, Low valence": dictionaries["high_energy_low_valence"],
        "High energy, High valence": dictionaries["high_energy_high_valence"]
    }
    
    playlist_ids = {}


    for playlist_name, tracks in playlist_data.items():
        data = {
            "name": playlist_name,
            "description": f"Playlist for {playlist_name}",
            "public": False
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            playlist_info = response.json()
            playlist_ids[playlist_name] = playlist_info["id"]
        else:
            continue


        for playlist_name, tracks in playlist_data.items():
            if playlist_name in playlist_ids and tracks:
                track_ids = list(tracks.keys())
                for i in range(0, len(track_ids), 100):
                    track_chunk = track_ids[i:i+100]
                    track_uris = [f"spotify:track:{track_id}" for track_id in track_chunk]

                    add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_ids[playlist_name]}/tracks"
                    add_tracks_data = {
                        "uris": track_uris
                    }

                    track_response = requests.post(add_tracks_url, headers=headers, json=add_tracks_data)
                    if track_response.status_code != 201:
                        print("fdnjkfn")
    return "Playlists created successfully!"
    
@app.route('/create_mood_playlists')
def create_mood_playlists():
    user_id = get_username()
    track_features = get_energy()
    dictionaries = create_mood_dictionaries(track_features)
    create_playlists(user_id, dictionaries)
    return jsonify({"status": "Playlists created!"})

@app.route('/genre_seeds')
def get_genres():
    token = session.get("access_token")
    url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"

    headers = {"Authorization": "Bearer " + token}

    response = requests.get(url, headers=headers)

    genre_seeds = response.json().get('seeds', [])
    genres = [genre["genre"] for genre in genre_seeds]
    return jsonify(genres)


if __name__ == "__main__":
    app.run(port=5000, debug=True)