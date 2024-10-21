from flask import Flask
from authentication import SpotifyAuth
from playlists import PlaylistManager
import os

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
auth = SpotifyAuth(app)
playlist_manager = PlaylistManager(app)

@app.route("/login")
def  login():
    return auth.login()

@app.route("/callback")
def callback():
    return auth.callback()

@app.route("/token")
def show_token():
    return auth.show_token()

@app.route("/artist_dictionary")
def artist_dictionary():
    return auth.artist_dictionary()

@app.route("/final_dictionary", methods=["GET"])
def final_dictionary():
    return auth.final_dictionary()

@app.route("/genre_counts")
def genre_counts():
    return auth.count_genres()

@app.route("/json_dictionary")
def json_dictionary():
    return auth.json_dictionary()

@app.route("/genre_dictionary")
def genre_dictionary():
    return auth.genre_dictionaries

@app.route("/valence_dictionary")
def valence_dictionary():
    return playlist_manager.valence_dictionary()

@app.route("/mixed_dictionary")
def mixed_dictionary():
    return playlist_manager.mixed_dictionary()
#final_dictionary = self.get_user_saved_track()
        #sorted_genre_count = dict(sorted(final_dictionary.items(), key=lambda item: item[1], reverse=True))
        #return jsonify(sorted_genre_count)
@app.route("/create_mood_playlists")
def create_mood_playlists():
    return playlist_manager.create_mood_playlists()

@app.route("/genre_seeds")
def genre_seeds():
    return playlist_manager.get_genres()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
