from flask import session, redirect, request, jsonify
import requests
import base64
import json
import urllib.parse
from config import Config
import secrets
import string
import webbrowser
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SpotifyAuth:
    def __init__(self, app):
        self.app = app
        self.client_id = Config.CLIENT_ID
        self.client_secret = Config.CLIENT_SECRET
        self.redirect_uri = Config.REDIRECT_URI

    def login(self):
        state = self.token_urlsafe(16)
        scope = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private"
        query_parameters = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state,
            "show_dialog": True
        }
        auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(query_parameters)
        return redirect(auth_url)
    
    def callback(self):
        code = request.args.get("code")
        token_request = {
            "url": "https://accounts.spotify.com/api/token",
            "data": {
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }
        }
        auth_credentials = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_credentials.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + auth_base64
        }

        response = requests.post(token_request["url"], data=token_request["data"], headers=headers)
        json_response = response.json()

        session["access_token"] = json_response["access_token"]
        return redirect("/token")
    
    def show_token(self):
        token = session.get("access_token")
        return "Your access token is " + token
    
    def token_urlsafe(self, length):
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def artist_dictionary(self):
        dictionary = self.get_artist_id()
        return jsonify(dictionary)

    def final_dictionary(self):
        final_dictionaryy = self.get_user_saved_track()
        return jsonify(final_dictionaryy)

    def pass_dict(self):
        genre_dictionary = self.get_user_saved_track()
        genre_count = self.count_genres(genre_dictionary)
        sorted_genre_count = sorted(genre_count.items(), key=lambda item: item[1], reverse=True)
        sorted_list = [{"genre": genre, "count": count} for genre, count in sorted_genre_count]

        return jsonify(sorted_list)

    def count_genres(self, artist_song_dict):
        genre_count = {}

        for artist_data in artist_song_dict.values():
            genres = artist_data.get("genres", [])

            for genre in genres:
                if genre in genre_count:
                    genre_count[genre] += 1
                else:
                    genre_count[genre] = 1
        return genre_count

    def json_dictionaryy(self):
        track_dictionary = self.get_user_saved_track()
        return jsonify(track_dictionary)

    def get_user_saved_track(self):
        token = session.get("access_token")
        track_url = "https://api.spotify.com/v1/me/tracks"
        headers = {"Authorization": "Bearer " + token}
        limit = 50
        offset = 0
        track_dictionary = {}

        artist_genres = self.get_genres()

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            response = requests.get(track_url, headers=headers, params=params)
            data = response.json()

            for item in data["items"]:
                track = item["track"]
                track_id = track["id"]
                track_name = track["name"]
                first_artist = track["artists"][0]
                artist_id = first_artist["id"]

                if artist_id not in track_dictionary:
                    artist_name = artist_genres.get(artist_id, {}).get("name", "Unknown Artist")
                    track_dictionary[artist_id] = {
                        "artist_name": artist_name,
                        "genres": artist_genres.get(artist_id, {}).get("genres", []),
                        "songs": [],
                        "track_ids": []
                    }

                if track_name not in track_dictionary[artist_id]["songs"]:
                    track_dictionary[artist_id]["songs"].append(track_name)
                    track_dictionary[artist_id]["track_ids"].append(track_id)
            if data["next"] is None:
                break

            offset += limit

        final_dictionary = {}

        for artist_id, info in track_dictionary.items():
            final_dictionary[info["artist_name"]] = {
                "genres": info["genres"],
                "songs": info["songs"],
                "track_ids": info["track_ids"]
            }

        return final_dictionary

    def get_track_id(self):
        id_dictionary = self.get_user_saved_track()
        track_ids = []
        logger.debug(f"id_dictionary: {id_dictionary}")
        for artist_info in id_dictionary.values():
            track_ids.extend(artist_info["track_ids"])
        return track_ids
    
    def get_artist_id(self):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/me/tracks"
        header = {"Authorization": "Bearer " + token }
        limit = 50
        offset = 0
        artist_dictionary = {}

        unique_artists = set()
        while True:

            params = {
                "limit": limit,
                "offset": offset
            }

            response = requests.get(url, headers=header, params=params)

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

    def get_genres(self):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/artists/"
        header = {"Authorization": "Bearer " + token }

        test_dictionary = self.get_artist_id()
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
    
    def get_genre_seeds(self):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
        headers = {"Authorization": "Bearer " + token}

        response = requests.get(url, headers=headers)

        genre_seeds = response.json().get("genres", [])
        return jsonify(genre_seeds)
