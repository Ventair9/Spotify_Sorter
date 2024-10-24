import requests
from flask import session, jsonify

class PlaylistManager:
    def __init__(self, app):
        self.app = app

    def get_username(self):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/me"
        header = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=header)
        return response.json()["id"]


    def create_playlist(self, user_id, dictionaries):
        token = session.get("access_token")
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = {
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
        dictionaries = {
            "low_energy_low_valence": {},
            "low_energy_high_valence": {},
            "girly": {},
            "high_energy_low_valence": {}
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

            if valence <= 0.3 and energy <= 0.5 and danceability <0.75 and speechiness <= 0.12:
                dictionaries["low_energy_low_valence"][track_id] = features
            elif valence >= 0.7 and energy >= 0.6 and acousticness <= 0.6 and speechiness <= 0.1:
                dictionaries["girly"][track_id] = features
        return dictionaries

    def valence_dictionary(self):
        dictionary = self.get_energy()
        return jsonify(dictionary)

    def mixed_dictionary(self):
        mixed_dictionary = self.get_energy()
        dictionaries = self.create_mood_dictionaries(mixed_dictionary)

        return jsonify(dictionaries)