from flask import Flask
from authentication import SpotifyAuth
from playlists import PlaylistManager
import os
from lyrics_analysis import lyricsAnalysis

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
auth = SpotifyAuth(app)
playlist_manager = PlaylistManager(app)
lyrics = lyricsAnalysis(app)

@app.route("/login") #check
def  login():
    return auth.login()

@app.route("/geniuslogin")
def geniuslogin():
    return lyrics.OAUTH2()

@app.route("/geniuscallback")
def geniuscallback():
    return lyrics.callback()

@app.route("/geniustoken")
def geniustoken():
    return lyrics.show_genius_token()

@app.route("/create_depression_playlist", methods=["POST", "GET"])
def create_depression_playlist():
    result = lyrics.create_depression_playlist()
    return result

@app.route("/callback") # check
def callback():
    return auth.callback()

@app.route("/token") # check
def show_token():
    return auth.show_token()

@app.route("/artist_dictionary") # check = artist id,
def artist_dictionary():
    return auth.artist_dictionary()

@app.route("/final_dictionary", methods=["GET"]) # check = artist, songs and genres
def final_dictionary():
    return auth.final_dictionary()

@app.route("/genre_counts") # check = genres, counts
def genre_counts():
    return auth.pass_dict()

@app.route("/json_dictionary") # check  
def json_dictionary():
    return auth.json_dictionaryy()

@app.route("/genre_dictionary") # check = id, genres, name
def genre_dictionary():
    return auth.get_genres()

@app.route("/valence_dictionary") # check
def valence_dictionary():
    return playlist_manager.valence_dictionary()

@app.route("/mixed_dictionary") # check
def mixed_dictionary():
    return playlist_manager.mixed_dictionary()

@app.route("/create_mood_playlists") # check
def create_mood_playlists():
    return playlist_manager.create_mood_playlists()

@app.route("/genre_seeds")
def get_seeds():
    return auth.get_genre_seeds()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
