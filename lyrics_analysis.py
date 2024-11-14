from flask import session, request, jsonify, redirect
import urllib.parse
from textblob import TextBlob
import requests
from config import Config
import base64
import secrets
import string
from playlists import PlaylistManager
from bs4 import BeautifulSoup

class lyricsAnalysis():
    def __init__(self, app):
        self.app = app
        self.GENIUS_id = Config.GENIUS_ID
        self.GENIUS_secret = Config.GENIUS_SECRET
        self.GENIUS_uri = Config.GENIUS_URI
        self.playlist_manager = PlaylistManager(app)

    def OAUTH2(self):
        state = self.token_urlsafe(16)
        scope = ""
        query_parameters = {
            "client_id": self.GENIUS_id,
            "response_type": "code",
            "redirect_uri": self.GENIUS_uri,
            "scope": scope,
            "state": state,
            "show_dialog": True
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

        session["access_token"] = json_response["access_token"]
        return redirect("/geniustoken")
    
    def show_genius_token(self):
        token = session.get("access_token")
        return "Your access token is " + token
    
    def token_urlsafe(self, length):
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

    def get_lyrics_for_depression_playlist(self):
        token = session.get("access_token")

        headers = {
            "Authorization": "Bearer " + token
        }

        filtered_depression_songs = []

        for track in self.playlist_manager.depression_playlist:
            search_query = f"{track["title"]} {track["artist"]}"
            search_url = f"https://api.genius.com/search?q{urllib.parse.quote(search_query)}"
            response = requests.get(search_url, headers=headers)

            if response.status_code == 200:
                search_results = response.json()
                hits = search_results.get("response", {}).get("hits", [])
                if hits:
                    song_id = hits[0]["result"]["id"]
                    lyrics_url = f"https://api.genius.com/songs/{song_id}"
                    lyrics_response = requests.get(lyrics_url, headers=headers)

                    if lyrics_response.status_code == 200:
                        song_data = lyrics_response.json()
                        lyrics_path = song_data["response"]["song"]["lyrics"]

                        lyrics_page = requests.get(lyrics_path)
                        soup = BeautifulSoup(lyrics_page.content, "html.parser")
                        lyrics = soup.find("div", class_="lyrics").get_text() if soup.find("div", class_="lyrics") else ""

                        sentiment_score = self.analyze_lyrics_sentiment(lyrics)
                        print(f"Sentiment score for {track['title']} by {track['artist']}: {sentiment_score}")

                        if sentiment_score <= -0.1:
                            filtered_depression_songs.append(track)

                    else:
                        print("Error")
                else:
                    print("error")
            else:
                print("errorr")

        self.depression_songs = filtered_depression_songs

    def analyze_lyrics(self, lyrics):

        analysis = TextBlob(lyrics)

        sentiment_score = analysis.sentiment.polarity
        return sentiment_score

    def create_depression_playlist(self):
        user_id = self.playlist_manager.get_username()
        track_features = self.playlist_manager.get_energy()
        dictionaries = self.playlist_manager.create_mood_dictionaries(track_features)

        self.get_lyrics_for_depression_playlist()

        for track in self.playlist_manager.depression_songs:
            dictionaries["depression"][track["track_id"]] = track_features[track["track_id"]]

        self.playlist_manager.create_playlist(user_id, dictionaries)
        return jsonify({"status": "playlists created successfully"})

    


  