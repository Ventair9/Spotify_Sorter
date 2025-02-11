import requests
from flask import session, jsonify
from authentication import SpotifyAuth


class PlaylistManager:
    def __init__(self, app):
        self.app = app
        self.authentication = SpotifyAuth(app)

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
            "High energy, High valence": dictionaries["girly"],
            "Deutschrap": dictionaries["deutschrap"],
            "Russian": dictionaries["russian"],
            "Pop": dictionaries["pop"],
            "KPop": dictionaries["kpop"],
            "Depression": dictionaries["depression"],
            "Rock": dictionaries["rock"],
            "Gangster Rap": dictionaries["gangster_rap"],
            "Emo Rap": dictionaries["emo_rap"],
            "Soundtracks": dictionaries["soundtracks"]
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
            print(f"Playlist: {playlist_name}")
            print(f"Track count: {len(tracks)}")
            print(f"Track IDs: {list(tracks.keys())[:5]}")
            if playlist_name in playlist_ids and tracks:
                track_ids = list(tracks.keys())

                for i in range(0, len(track_ids), 100):
                    track_chunk = track_ids[i:i+100]
                    track_uris = [f"spotify:track:{track_id}" for track_id in track_chunk]

                    if track_uris:
                        add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_ids[playlist_name]}/tracks"
                        add_tracks_data = {
                            "uris": track_uris
                        }

                        track_response = requests.post(add_tracks_url, headers=headers, json=add_tracks_data)
                        
                            
        return dictionaries


    def create_mood_playlists(self):
        user_id = self.get_username()
        track_features = self.get_energy()
        dictionaries = self.create_mood_dictionaries(track_features)
        self.create_playlist(user_id, dictionaries)
        return jsonify({"status": "playlists created successfully"})
    
    def get_audio_features(self):
        token = session.get("access_token")
        print(token)
        audio_url = "https://api.spotify.com/v1/audio-features"
        header = {"Authorization": "Bearer " + token}

        track_ids = self.authentication.get_track_id()
        print(track_ids)
        track_features = {}

        for i in range(0, len(track_ids), 100):
            track_id_chunk = track_ids[i:i+100]
            track_id_string = ",".join(track_id_chunk)
            response = requests.get(f"{audio_url}?ids={track_id_string}", headers=header)
            print(response)
            audio_features = response.json()
            print(audio_features)

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
                    loudness = track["loudness"]

                    track_features[track_id] = {
                        "valence": valence,
                        "energy": energy,
                        "tempo": tempo,
                        "danceability": danceability,
                        "speechiness": speechiness,
                        "acousticness": acousticness,
                        "mode": mode,
                        "key": key,
                        "instrumentalness": instrumentalness,
                        "loudness": loudness
                    }
        return track_features
    
    def create_mood_dictionaries(self, track_features):

        dictionaries = {
            "low_energy_low_valence": {},
            "low_energy_high_valence": {},
            "girly": {},
            "high_energy_low_valence": {},
            "deutschrap": {},
            "russian": {},
            "pop": {},
            "kpop": {},
            "depression": {},
            "rock": {},
            "gangster_rap": {},
            "emo_rap": {},
            "soundtracks": {}
        }

        final_dictionary = self.authentication.get_user_saved_track()
        track_to_genres = {}

        for artist_name, info in final_dictionary.items():
            genres = info["genres"]
            track_ids = info["track_ids"]
            for track_id in track_ids:
                track_to_genres[track_id] = genres

        for track_id, features in track_features.items():
            valence = features["valence"]
            energy = features["energy"]
            mode = features["mode"]
            danceability = features["danceability"]
            speechiness = features["speechiness"]
            tempo = features["tempo"]
            acousticness = features["acousticness"]
            instrumentalness = features["instrumentalness"]

            track_genres = track_to_genres.get(track_id, [])

            if  any(genre.lower() in ["russian dance", "russian hip hop", "russian alt pop", "russian dance"] for genre in track_genres):
                dictionaries["russian"][track_id] = features
            elif valence <= 0.3 and energy <= 0.5 and danceability <0.75 and speechiness <= 0.12:
                dictionaries["low_energy_low_valence"][track_id] = features
            elif valence >= 0.7 and energy >= 0.6 and acousticness <= 0.6 and speechiness <= 0.1:
                dictionaries["girly"][track_id] = features
            elif any(genre.lower() in ["german hip hop"] for genre in track_genres):
                dictionaries["deutschrap"][track_id] = features
            elif any(genre.lower() in ["pop", "dance pop", "pop dance"] for genre in track_genres) and not any("k-pop" in genre.lower() for genre in track_genres) and valence >= 0.5:
                dictionaries["pop"][track_id] = features
            elif any(genre.lower() in ["k-pop"] for genre in track_genres):
                dictionaries["kpop"][track_id] = features
            elif any(genre.lower() in ["rock"] for genre in track_genres):
                dictionaries["rock"][track_id] = features
            elif any(genre.lower() in ["emo rap"] for genre in track_genres):
                dictionaries["emo_rap"][track_id] =  features
            elif any(genre.lower() in ["rap", "west coast rap", "dirty south rap", "gangster rap"] for genre in track_genres):
                dictionaries["gangster_rap"][track_id] = features
            elif valence <= 0.4 and instrumentalness <= 0.01:
                dictionaries["depression"][track_id] = features
            elif any(genre.lower() in ["soundtrack", "scorescore", "theme"] for genre in track_genres):
                dictionaries["soundtracks"][track_id] = features

        return dictionaries

    def valence_dictionary(self):
        dictionary = self.get_audio_features()
        return jsonify(dictionary)

    def mixed_dictionary(self):
        mixed_dictionary = self.get_audio_features()
        dictionaries = self.create_mood_dictionaries(mixed_dictionary)

        return jsonify(dictionaries)
