import json
import os
from requests.auth import HTTPBasicAuth
import app

# --- get tweet text from env ---
AUTOMATED_TWEET = os.environ.get("AUTOMATED_TWEET")

if not AUTOMATED_TWEET:
    raise RuntimeError(
        "AUTOMATED_TWEET env var not set. Cron job has nothing to post."
    )

x = app.make_token()
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
token_url = "https://api.x.com/2/oauth2/token"

t = app.r.get("token")
if not t:
    raise RuntimeError("No token found in Redis under key 'token'. Re-auth via / first.")

data = json.loads(t.decode("utf-8"))

if not client_id or not client_secret:
    raise RuntimeError("Missing CLIENT_ID/CLIENT_SECRET in environment.")

refreshed_token = x.refresh_token(
    token_url=token_url,
    refresh_token=data.get("refresh_token"),
    auth=HTTPBasicAuth(client_id, client_secret),
    include_client_id=True,
)

app.r.set("token", json.dumps(refreshed_token))
payload = {"text": AUTOMATED_TWEET}
app.create_post(payload, refreshed_token)
