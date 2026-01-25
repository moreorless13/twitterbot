import base64
import hashlib
from dotenv import load_dotenv
import os
import re
import json
import requests
import redis
from urllib.parse import urlparse
from requests.auth import AuthBase, HTTPBasicAuth
from requests_oauthlib import OAuth2Session, TokenUpdated
from flask import Flask, request, redirect, session, url_for, render_template


load_dotenv()

r = None
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    _redis = redis.from_url(redis_url)
    _redis.ping()
    r = _redis
except Exception:
    r = None
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY env var not set. Cannot start.")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

auth_url = "https://x.com/i/oauth2/authorize"
token_url = "https://api.x.com/2/oauth2/token"
redirect_uri = os.getenv("REDIRECT_URI")

scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]


def generate_pkce():
    verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
    verifier = re.sub("[^a-zA-Z0-9]+", "", verifier)

    challenge = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(challenge).decode("utf-8")
    challenge = challenge.replace("=", "")
    return verifier, challenge

def make_token():
    return OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        scope=scopes)


 
def create_post(payload, token):
     print(("Posting!"))
     return requests.request(
     "POST",
     "https://api.x.com/2/tweets",
     json=payload,
     headers={
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
     },
    )
     
@app.route("/")
def demo():
    code_verifier, code_challenge = generate_pkce()
    oauth = make_token()
    authorization_url, state = oauth.authorization_url(
        auth_url,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    session["oauth_state"] = state
    session["code_verifier"] = code_verifier
    return redirect(authorization_url)

@app.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    code = request.args.get("code")
    code_verifier = session.get("code_verifier")
    state = session.get("oauth_state")
    if not code or not code_verifier or not state:
        return {"error": "Missing OAuth state/code_verifier/code"}, 400

    oauth = OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        scope=scopes,
        state=state,
    )
    token = oauth.fetch_token(
        token_url,
        client_secret=client_secret,
        code_verifier=code_verifier,
        code=code,
    )

    session["token"] = token
    if r is not None:
        try:
            r.set("token", json.dumps(token))
        except Exception:
            pass
    payload = {"text": "Hello, world! This is an automated tweet."}
    tweet_resp = create_post(payload, token)
    try:
        body = tweet_resp.json()
    except ValueError:
        body = {"error": "Non-JSON response from X API", "text": tweet_resp.text}
    return body, tweet_resp.status_code

if __name__ == "__main__":
    parsed = urlparse(redirect_uri) if redirect_uri else None
    host = parsed.hostname if parsed and parsed.hostname else "127.0.0.1"
    port = parsed.port if parsed and parsed.port else 5000
    app.run(host=host, port=port, debug=True)