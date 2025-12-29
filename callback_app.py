#!/usr/bin/env python3

import os
from flask import Flask, request

app = Flask(__name__)


@app.get("/")
def index():
    return "OK", 200


@app.get("/oauth/callback")
@app.get("/callback")
def oauth_callback():
    full_url = request.url

    # Display the full URL so you can copy/paste it into:
    #   python twitter_bot.py --callback-url "<FULL_URL>"
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>OAuth Callback</title>
    <style>
      body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 32px; line-height: 1.4; }}
      pre {{ white-space: pre-wrap; word-break: break-all; padding: 12px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; }}
      button {{ padding: 10px 14px; border-radius: 6px; border: 1px solid #d0d7de; background: white; cursor: pointer; }}
      .muted {{ color: #57606a; }}
    </style>
  </head>
  <body>
    <h1>OAuth callback received</h1>
    <p class=\"muted\">Copy the full URL below (it contains <code>state</code> and <code>code</code>).</p>

    <pre id=\"url\">{full_url}</pre>
    <button id=\"copy\">Copy URL</button>
    <p id=\"status\" class=\"muted\"></p>

    <script>
      const url = document.getElementById('url').textContent;
      document.getElementById('copy').addEventListener('click', async () => {{
        try {{
          await navigator.clipboard.writeText(url);
          document.getElementById('status').textContent = 'Copied to clipboard.';
        }} catch {{
          document.getElementById('status').textContent = 'Copy failed — manually select and copy the URL.';
        }}
      }});
    </script>
  </body>
</html>""" , 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
