from flask import session, redirect, request, jsonify
import requests
import base64
import json
import urllib.parse
from config import Config
import secrets
import string

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
        json_response = response.loads(response.content)

        session["access_token"] = json_response["access_token"]
        return redirect("/token")
    
    def show_token(self):
        token = session.get("access_token")
        return "Your access token is " + token
    
    def token_urlsafe(self, length):
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def artist_dictionary(self)
        pass

    def final_dictionary(self):
        pass

    def genre_counts(self):
        pass

    def json_dictionary(self):
        pass

    def get_user_saved_track(self):
        pass

    def get_artist_id(self):
        pass

    def get_artis(self):
        pass
    
