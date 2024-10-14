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

"""
gotta start writing comments in here innit, program is built to interact with the spotify web api to sort liked songs into designated
playlists chosen by the user
"""
#using the dotenv to store user sensitive data for security reasons
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"

def token_urlsafe(length):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))
#creating the login landing page for the user to login to spotify
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
#all of this just to return the token lolz

@app.route('/token')
def show__token():
    token = session.get('access_token')
    return "Your access token is " + token
    
#i want to rewrite this function later on, but for now, getting the artist_ids and names to return the artists associated genres later
def get_artist_id():
    token = session.get("access_token")
    track_url = "https://api.spotify.com/v1/me/tracks"
    header = {"Authorization": "Bearer " + token}
    limit = 50
    offset = 0
    artist_dictionary = {}

    unique_artists = set()
    while True:

        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = requests.get(track_url, headers=header, params=params)

        data = response.json()

        for item in data["items"]:
            tracks = item["track"]
            artists = tracks["artists"]

            for artist in artists:
                first_artist = artists[0]
                artist_id = first_artist["id"]
                artist_name = first_artist["name"]

                if artist_id not in unique_artists:
                    unique_artists.add(artist_id)
                    artist_dictionary[artist_id] = artist_name

        if data["next"] is None:
            break

        offset += limit

    return artist_dictionary

@app.route("/artist_dictionary")
def artist_dictionary():
    dictionary = get_artist_id()

    return jsonify(dictionary)

# lowkey the same function as above, repetitive code yada yada but i gotta fix this later for sure.
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

            for artist in artists["artists"]:
                artists = artist["artists"]
                artist_name = artists["name"]

                track_dictionary[artist_name] = track_name

            if data['next'] is None:
                break


            offset += limit

        return track_dictionary

@app.route('/json_dictionary')
def json_dictionary():
    track_dictionary = get_user_saved_track()

    return jsonify(track_dictionary)

    #function for getting the artist of the tracks
def get_artist():
    token = session.get("access_token")
    url = "https://api.spotify.com/v1/artists/"
    header = {"Authorization": "Bearer " + token}

    test_dictionary = get_artist_id()
    artist_ids = list(test_dictionary.keys())

    artist_genres = {}

    for i in range(0, len(artist_ids), 50):
        artist_id_chunk = artist_ids[i:i+50]
        artist_id_string = ",".join(artist_id_chunk)

        response = requests.get(f"{url}?ids={artist_id_string}", headers=header)
        artist_data = response.json()

        for artist in artist_data["artists"]:
            genres = artist.get("genres", [])
            id = artist.get("id")
            name = artist.get("name")

            artist_genres[id] = {
                "genres": genres,
                "name": name
            }
    return artist_genres

@app.route('/genre_dictionary')

def genre_dictionaries():
    genre_dictionary = get_artist()

    return jsonify(genre_dictionary)

    #function for getting the different song values and parameters
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
                tempo = track["tempo"]
                danceability = track["danceability"]
                speechiness = track["speechiness"]
                acousticness = track["acousticness"]
                mode = track["mode"]
                key = track["key"]
                instrumentalness = track["instrumentalness"]

                track_features[track_id] = {
                    "valence": valence,
                    "energy": energy,
                    "tempo": tempo,
                    "danceability": danceability,
                    "speechiness": speechiness,
                    "acousticness": acousticness,
                    "mode": mode,
                    "key": key,
                    "instrumentalness": instrumentalness
                }
                

    return track_features

""" using spotify's audio analysis in order to create playlists, implementing logic in order to combine this with genres to make more
specific playlists later on.
"""
def create_mood_dictionaries(track_features):

    dictionaries = {
        "low_energy_low_valence": {},
        "high_energy_high_valence": {},
        "girly": {},
        "high_energy_low_valence": {},
    }

    for track_id, features in track_features.items():
        valence = features["valence"]
        energy = features["energy"]
        mode = features["mode"]
        danceability = features["danceability"]
        speechiness = features["speechiness"]
        tempo = features["tempo"]
        acousticness = features["acousticness"]
        instrumentalness = features["instrumentalness"]

        if valence <= 0.3 and energy <= 0.5 and danceability <= 0.75 and speechiness <= 0.12:
            dictionaries["low_energy_low_valence"][track_id] = features
        elif valence >= 0.7 and energy >= 0.6 and acousticness <= 0.6 and speechiness <= 0.1:
            dictionaries["high_energy_high_valence"][track_id] = features
        elif valence >= 0.7 and energy >= 0.5 and danceability >= 0.7 and speechiness <= 0.1:
            dictionaries["girly"][track_id] = features
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
#gotta get the username in order to create playlists
def get_username():
    token = session.get("access_token")
    url = "https://api.spotify.com/v1/me"
    header = {"Authorization": "Bearer " + token}

    response = requests.get(url, headers=header)
    data = response.json()

    user_id = data['id']
    return user_id
#function to create playlists for the user. gotta expand this later on aswell.
def create_playlists(user_id, dictionaries):
    token = session.get("access_token")
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers =  {
        
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    playlist_data = {
        "Low energy, Low valence": dictionaries["low_energy_low_valence"],
        "Low energy, High valence": dictionaries["girly"],
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
            added_tracks = set()
                
            for i in range(0, len(track_ids), 100):
                track_chunk = track_ids[i:i+100]
                track_uris = [f"spotify:track:{track_id}" for track_id in track_chunk if track_id not in added_tracks]

                if track_uris:
                     add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_ids[playlist_name]}/tracks"
                     add_tracks_data = {
                         "uris": track_uris
                    }

                track_response = requests.post(add_tracks_url, headers=headers, json=add_tracks_data)
                if track_response.status_code == 201:
                    added_tracks.update(track_uris)
                else:
                    print("Error")
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

#?????? link artist genres to saved songs by checking saved songs first artist, extract genre into dictionary,