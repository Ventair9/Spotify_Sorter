import requests
from flask import session, jsonify

class PlaylistManager:
    def __init__(self):
        self.token = self.get_access_token()

    def get_username(self):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/me"
        header = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=header)
        return response.json()["id"]


    def create_playlist(self, user_id, dictionaries):
        token = session.get("access_token")
        pass

    def create_mood_playlists(self):
        user_id = self.get_username()
        track_features = self.get_energy()
        dicitonaries = self.create_mood_dictionaries(track_features)
        self.create_playlists(user_id, dicitonaries)
        return jsonify({"status": "playlists created successfully"})
    
    def get_energy(self):
        token = session.get("access_token")
        audio_url = "https://api.spotify.com/v1/audio-features"
        header = {"Authorization": "Bearer " + token}

        track_dictionary = self.get_user_saved_track()
        track_ids = list(track_dictionary.keys())

        track_features = {}

        for i in range(0, len(track_ids), 100):
            track_id_chunk = track_ids[i:i+100]
            track_id_string = ",".join(track_id_chunk)

            response = requests.get(f"{self.audio_url}?ids={track_id_string}", headers=header)
            audio_features = response.json()

            for track in audio_features.get("audio_features", []):
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


    def create_mood_dictionaries(self, track_features):
        pass

    def valence_dictionary(self):
        pass

    def mixed_dictionary(self):
        pass

    def get_genres(self):
        pass