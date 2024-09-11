#1 application to spotify account service requests authorization to access data -> user login, authorize access
#for that, client_id, response_type, redirect_uri, state, scope
#user goes back to application
#2 application requests access and refresh tokens with client_id, client_secret, grant_type, code, redirect_uri
#spotify account service then returns access and refresh tokens if done corretly
#back to application
#3 use access token in requests to the web api -> give access token to accounts service, service returns json object(requested data)
#then, go back to application
#4 user access token in requests to web api, you give your access token, spotify accounts service gives back a json obect and a
#access token, then goes back to step 3

from flask import Flask, redirect, request
import requests
import random
import string
import urllib.parse
from urllib.parse import urlparse, parse_qs 
from dotenv import load_dotenv
import os
import base64
import json

load_dotenv()

app = Flask(__name__)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"

def generate_random_string(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/login")
def login():
    state = generate_random_string(16)
    scope = "user-read-private user-read-email user-library-read"

    query_parameters = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "show_dialog": True
    }

    spotify_auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(query_parameters)
    return redirect(spotify_auth_url)

@app.route('/callback')
def callback():
    url = request.url
    parsed_url = urlparse(url)
    query_parameters2 = parse_qs(parsed_url.query)

    code = query_parameters2.get("code", [None])[0]
    state = query_parameters2.get("state", [None])[0]

    query_parameters2 = {
        "url": "https://accounts.spotify.com/api/token",
        "data": {

        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
        }
    }
    auth_credentials = client_id + ":" + client_secret
    auth_bytes = auth_credentials.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    headers = {

        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + auth_base64
    }
    response = requests.post(query_parameters2['url'], data=query_parameters2['data'], headers=headers)
    json_response = json.loads(response.content)
    token = json_response["access_token"]
    return token

def get_user_saved_track(token):
    track_url = "https://api.spotify.com/v1/me/tracks"
    header = "Authorization: Bearer" + token

    response = requests.get(track_url, headers=header)


if __name__ == "__main__":
    app.run(port=5000)