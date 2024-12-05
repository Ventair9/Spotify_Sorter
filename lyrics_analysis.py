from flask import session, request, jsonify, redirect
import urllib.parse
from textblob import TextBlob
import requests
from config import Config
import base64
import secrets
import string
from playlists import PlaylistManager
from authentication import SpotifyAuth
from bs4 import BeautifulSoup


class LyricsAnalysis():
    def __init__(self, app):
        self.app = app
        self.GENIUS_id = Config.GENIUS_ID
        self.GENIUS_secret = Config.GENIUS_SECRET
        self.GENIUS_uri = Config.GENIUS_URI
        self.GENIUS_token = Config.GENIUS_TOKEN
        self.playlist_manager = PlaylistManager(app)
        self.authentication = SpotifyAuth(app)
        self.depression_candidates = {}
    """
    def OAUTH2(self):
        state = self.token_urlsafe(16)
        scope = ""
        query_parameters = {
            "client_id": self.GENIUS_id,
            "response_type": "code",
            "redirect_uri": self.GENIUS_uri,
            "scope": scope,
            "state": state
        }
        auth_url = "https://api.genius.com/oauth/authorize?" + urllib.parse.urlencode(query_parameters)
        return redirect(auth_url)
    
    def callback(self):
        code = request.args.get("code")
        token_request = {
            "url": "https://api.genius.com/oauth/token",
            "data": {
                "code": code,
                "redirect_uri": self.GENIUS_uri,
                "client_secret": self.GENIUS_secret,
                "client_id": self.GENIUS_id,
                "grant_type": "authorization_code",
                "response_type": "code"
            }
        }
        auth_credentials = f"{self.GENIUS_id}:{self.GENIUS_secret}"
        auth_bytes = auth_credentials.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + auth_base64
        }
        
        response = requests.post(token_request["url"], data=token_request["data"], headers=headers)
        json_response = response.json()
        print("genius api response", json_response)
        return redirect("/geniustoken")
    """

    def show_genius_token(self):
        genius_token = self.GENIUS_token
        return "Your access token is " + genius_token
    
    def token_urlsafe(self, length):
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

    def prepare_candidates(self, track_features, final_dictionary, saved_tracks):
        self.depression_candidates = {}

        for track_id, features in track_features.items():
            valence = features["valence"]
            instrumentalness = features["instrumentalness"]

            if valence <= 0.4 and instrumentalness <= 0.01:

                for genre, tracks in final_dictionary.items():
                    for track_id, features in tracks.items():
                        for artist_name, info in saved_tracks.items():
                            if track_id in info["track_ids"]:
                                track_index = info["track_ids"].index(track_id)
                                track_name = info.get("track_names", [])[track_index] if "track_names" in info else "Unknown"

                                self.depression_candidates[track_id] = {
                                    "features": features,
                                    "artist": artist_name,
                                    "title": track_name
                                }
                                break

    def get_lyrics_for_depression_playlist(self):
        genius_token = self.GENIUS_token

        headers = {"Authorization": "Bearer " + genius_token}

        filtered_depression_songs = {}
        print("The start of the end")
        try:
            for track_id, track_info in self.depression_candidates.items():
                try:
                    search_query = f"{track_info["title"]} {track_info["artist"]}"
                    search_url = f"https://api.genius.com/search?q={urllib.parse.quote(search_query)}"
                    print(f"Searching for: {search_query}")
                    response = requests.get(search_url, headers=headers)

                    print(f"Search Response Status: {response.status_code}")
                    print(f"Response Content: {response.text}")

                    if response.status_code == 200:
                        search_results = response.json()
                        hits = search_results.get("response", {}).get("hits", [])
                        if not hits:
                            print(f"No hits found for {search_query}")
                            continue

                        song_id = hits[0]["result"]["id"]
                        lyrics_url = f"https://api.genius.com/songs/{song_id}"
                        lyrics_response = requests.get(lyrics_url, headers=headers)

                        if lyrics_response.status_code == 200:
                            song_data = lyrics_response.json()
                            lyrics_path = song_data["response"]["song"]["lyrics"]
                            lyrics_url = f"https://genius.com{lyrics_path}"

                            lyrics_page = requests.get(lyrics_path)
                            soup = BeautifulSoup(lyrics_page.content, "html.parser")
                            lyrics = soup.find("div", class_="lyrics").get_text() if soup.find("div", class_="lyrics") else ""

                            if lyrics:
                                sentiment_score = self.analyze_lyrics(lyrics)
                                print(f"Sentiment score for {track_info['title']} by {track_info['artist']}: {sentiment_score}")

                                if sentiment_score <= -0.1:
                                    filtered_depression_songs[track_id] = track_info["features"]

                            else:
                                print(f"No lyrics found for {search_query}")
                        else:
                            print(f"Failed to retrieve song data: {lyrics_response.status_code}")
                    else:
                        print(f"Search request failed: {response.status_code}")

                except Exception as track_error:
                    print(f"Error processing track {track_id}: {track_error}")

        except Exception as e:
                print(f"Unexpected error in get_lyrics_for_depression_playlist: {e}")

        return filtered_depression_songs
    
    def analyze_lyrics(self, lyrics):   

        analysis = TextBlob(lyrics)

        sentiment_score = analysis.sentiment.polarity
        return sentiment_score

    def create_depression_playlist(self):
        user_id = self.playlist_manager.get_username()
        track_features = self.playlist_manager.get_energy()
        final_dictionary = self.playlist_manager.create_mood_dictionaries(track_features)
        saved_tracks = self.authentication.get_user_saved_track() 
        self.prepare_candidates(track_features, final_dictionary, saved_tracks)

        filtered_depression_songs = self.get_lyrics_for_depression_playlist()


        dictionaries = self.playlist_manager.create_mood_dictionaries(track_features)
        dictionaries["depression"] = filtered_depression_songs

        self.playlist_manager.create_playlist(user_id, dictionaries)
        return jsonify({"status": "playlists created successfully"})
    print("somoene fucking help me then")