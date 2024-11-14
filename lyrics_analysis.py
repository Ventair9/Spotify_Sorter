from flask import session, request, jsonify, redirect
import urllib.parse
from textblob import Textblob
import requests
from config import Config
import base64
import secrets
import string

class lyricsAnalysis():
    def __init__(self, app):
        self.app = app
        self.client_id = Config.GENIUS_ID
        self.client_secret = Config.GENIUS_SECRET
        self.redirect_uri = Config.GENIUS_URI

    def OAUTH2(self):
        state = self.token_urlsafe(16)
        scope = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private"
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
                "client_secret": self.client_secret,
                "client_id": self.GENIUS_id,
                "grant_type": "authorization_code",
                "reponse_type": "code"
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
    


  