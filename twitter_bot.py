#!/usr/bin/env python3
"""Twitter Bot - Automated posting using Twitter API v2 with OAuth 2.0 (PKCE)."""

import os
import sys
import argparse
from urllib.parse import urlparse
from typing import Any
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import tweepy
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables from .env file
load_dotenv()

# Allow http:// redirects for local development only.
_redirect_uri = os.getenv('REDIRECT_URI', '')
if _redirect_uri.startswith('http://127.0.0.1') or _redirect_uri.startswith('http://localhost'):
    os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')


class TwitterBot:
    """Twitter Bot class for automated posting using Twitter API v2"""

    client_id: str
    client_secret: str | None
    redirect_uri: str
    access_token: str | None
    refresh_token: str | None
    
    def __init__(self):
        """Initialize the Twitter bot with OAuth 2.0 credentials"""
        # Get credentials from environment variables
        client_id = os.getenv('TWITTER_CLIENT_ID')
        client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        redirect_uri = os.getenv('REDIRECT_URI')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.refresh_token = os.getenv('TWITTER_REFRESH_TOKEN')

        self._env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        self._state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tweet_state.json')
        self._token_url = 'https://api.twitter.com/2/oauth2/token'
        self._scope = [
            'tweet.read',
            'tweet.write',
            'users.read',
            'offline.access',
        ]

        # In CI/server environments we typically don't want to write secrets/state back to disk.
        self._disable_persistence = (
            os.getenv('DISABLE_ENV_PERSIST', '').strip() == '1'
            or os.getenv('GITHUB_ACTIONS', '').strip().lower() == 'true'
        )

        # Validate required credentials
        if not client_id:
            raise ValueError(
                "Missing required credential: TWITTER_CLIENT_ID. Please check your .env file."
            )

        # Assign strongly-typed attributes after validation
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or ''

        # Initialize Twitter API client lazily after tokens are present
        self.client = None

    def _load_state(self) -> dict:
        if self._disable_persistence:
            return {}
        try:
            if not os.path.exists(self._state_path):
                return {}
            with open(self._state_path, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save_state(self, state: dict) -> None:
        if self._disable_persistence:
            return
        try:
            with open(self._state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f)
        except Exception:
            # Non-fatal: posting can still work without state persistence.
            pass

    def _load_tweet_messages(self) -> list[str]:
        """Load tweet messages from env.

        Preferred: TWEET_MESSAGES=msg1|msg2|msg3
        Fallback:  TWEET_MESSAGE=single message
        """
        raw_list = os.getenv('TWEET_MESSAGES')
        if raw_list and raw_list.strip():
            # Split by | and trim whitespace; ignore empties.
            messages = [m.strip() for m in raw_list.split('|') if m.strip()]
            return messages

        single = os.getenv('TWEET_MESSAGE', 'Hello from my automated Twitter bot!')
        return [single]

    def get_next_tweet_message(self) -> str:
        messages = self._load_tweet_messages()
        if not messages:
            raise ValueError('No tweet messages configured')

        mode = os.getenv('TWEET_ROTATION_MODE', 'sequential').strip().lower()
        if mode == 'time' and len(messages) >= 3:
            tz_name = os.getenv('TWEET_TIMEZONE', 'America/New_York').strip() or 'America/New_York'
            now = datetime.now(ZoneInfo(tz_name))
            # Default mapping for 3 posts/day: morning / afternoon / evening.
            # 00:00–11:59 -> messages[0]
            # 12:00–16:59 -> messages[1]
            # 17:00–23:59 -> messages[2]
            if now.hour < 12:
                return messages[0]
            if now.hour < 17:
                return messages[1]
            return messages[2]

        state = self._load_state()
        last_index = state.get('last_index')
        try:
            last_index_int = int(last_index) if last_index is not None else -1
        except Exception:
            last_index_int = -1

        next_index = (last_index_int + 1) % len(messages)
        state['last_index'] = next_index
        state['last_used_at'] = datetime.now().isoformat(timespec='seconds')
        self._save_state(state)

        return messages[next_index]
        
        # Validate credentials
        if not client_id:
            raise ValueError(
                "Missing required credential: TWITTER_CLIENT_ID. Please check your .env file."
            )

        if not redirect_uri:
            raise ValueError(
                "Missing required credential: REDIRECT_URI. Please check your .env file."
            )

        # Assign strongly-typed attributes after validation
        self.client_id: str = client_id
        self.redirect_uri: str = redirect_uri
        self.client_secret: str | None = client_secret
        
        # Initialize Twitter API v2 client with OAuth 2.0
        self.client: tweepy.Client | None = None

    @staticmethod
    def _is_missing_or_placeholder(value: str | None) -> bool:
        if not value:
            return True
        normalized = value.strip().lower()
        return normalized in {
            'your_access_token_here',
            'your_refresh_token_here',
            'your_client_id_here',
            'your_client_secret_here',
        }

    def _oauth_handler(self) -> tweepy.OAuth2UserHandler:
        if not self.redirect_uri:
            raise ValueError(
                "Missing required credential: REDIRECT_URI. Set it to your app callback URL."
            )

        client_secret: str | None
        if self._oauth2_client_auth_mode() == 'none':
            client_secret = None
        else:
            client_secret = self.client_secret

        return tweepy.OAuth2UserHandler(
            client_id=self.client_id,
            client_secret=client_secret,
            redirect_uri=self.redirect_uri,
            scope=self._scope,
        )

    @staticmethod
    def _oauth2_client_auth_mode() -> str:
        """Return OAuth2 client auth mode: 'auto' (default), 'basic', or 'none'."""
        raw = os.getenv('TWITTER_OAUTH2_CLIENT_AUTH', 'auto').strip().lower()
        if raw in {'none', 'basic'}:
            return raw
        return 'auto'

    def _basic_auth(self) -> HTTPBasicAuth | None:
        """Return HTTPBasicAuth for confidential clients, else None for public/PKCE clients."""
        mode = self._oauth2_client_auth_mode()
        if mode == 'none':
            return None
        if mode == 'basic' and self._is_missing_or_placeholder(self.client_secret):
            raise ValueError(
                "TWITTER_OAUTH2_CLIENT_AUTH=basic requires TWITTER_CLIENT_SECRET to be set."
            )
        if mode == 'auto' and self._is_missing_or_placeholder(self.client_secret):
            return None
        assert self.client_secret is not None
        return HTTPBasicAuth(self.client_id, self.client_secret)

    def _exchange_code_for_token(self, code: str, code_verifier: str) -> dict:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data: dict[str, str] = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier,
        }
        auth = self._basic_auth()
        # Public clients must include client_id in body (no Authorization header).
        if auth is None:
            data['client_id'] = self.client_id

        resp = requests.post(self._token_url, headers=headers, data=data, auth=auth, timeout=30)
        # Some Twitter app configs behave like public/PKCE clients even when a client secret exists.
        # If Twitter rejects the Basic-auth attempt with "Missing valid authorization header", retry as public.
        if (
            resp.status_code == 401
            and auth is not None
            and 'unauthorized_client' in resp.text
            and 'authorization header' in resp.text.lower()
        ):
            data_public = dict(data)
            data_public['client_id'] = self.client_id
            resp = requests.post(self._token_url, headers=headers, data=data_public, auth=None, timeout=30)

        if resp.status_code >= 400:
            raise Exception(f"Token exchange failed ({resp.status_code}): {resp.text}")
        return resp.json()

    def _refresh_token(self, refresh_token: str) -> dict:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data: dict[str, str] = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        auth = self._basic_auth()
        if auth is None:
            data['client_id'] = self.client_id

        resp = requests.post(self._token_url, headers=headers, data=data, auth=auth, timeout=30)
        if (
            resp.status_code == 401
            and auth is not None
            and 'unauthorized_client' in resp.text
            and 'authorization header' in resp.text.lower()
        ):
            data_public = dict(data)
            data_public['client_id'] = self.client_id
            resp = requests.post(self._token_url, headers=headers, data=data_public, auth=None, timeout=30)

        if resp.status_code >= 400:
            raise Exception(f"Token refresh failed ({resp.status_code}): {resp.text}")
        return resp.json()

    def get_authorization_url(self) -> str:
        """Return the OAuth 2.0 authorization URL for the configured client."""
        handler = self._oauth_handler()
        auth_url = handler.get_authorization_url()

        # Persist PKCE verifier/state so a later process can exchange the callback.
        code_verifier = getattr(getattr(handler, '_client', None), 'code_verifier', None)
        state = getattr(handler, '_state', None)
        if code_verifier:
            self._persist_env_value('TWITTER_OAUTH2_CODE_VERIFIER', code_verifier)
            os.environ['TWITTER_OAUTH2_CODE_VERIFIER'] = code_verifier
        if state:
            self._persist_env_value('TWITTER_OAUTH2_STATE', state)
            os.environ['TWITTER_OAUTH2_STATE'] = state

        return auth_url

    def exchange_callback_url_for_tokens(self, callback_url: str) -> dict:
        """Exchange the redirect/callback URL for OAuth 2.0 tokens and persist them to .env."""
        parsed = urlparse(callback_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("callback_url must be a full URL (e.g., http://127.0.0.1:5000/oauth/callback?...)")

        # Extract code/state from callback URL
        from urllib.parse import parse_qs
        query = parse_qs(parsed.query)
        code = (query.get('code') or [None])[0]
        returned_state = (query.get('state') or [None])[0]
        if not code:
            raise ValueError("callback_url is missing required query parameter: code")

        code_verifier = os.getenv('TWITTER_OAUTH2_CODE_VERIFIER')
        state = os.getenv('TWITTER_OAUTH2_STATE')
        if self._is_missing_or_placeholder(code_verifier) or self._is_missing_or_placeholder(state):
            raise ValueError(
                "Missing PKCE verifier/state. Run with --authorize again, then re-try --callback-url."
            )
        assert code_verifier is not None
        assert state is not None

        if returned_state and returned_state != state:
            raise ValueError("State mismatch. Re-run --authorize and try again with the new callback URL.")

        token = self._exchange_code_for_token(code=code, code_verifier=code_verifier)

        access_token = token.get('access_token')
        refresh_token = token.get('refresh_token')
        if self._is_missing_or_placeholder(access_token):
            raise Exception("OAuth exchange succeeded but no access_token was returned.")
        assert access_token is not None
        if self._is_missing_or_placeholder(refresh_token):
            # Some flows may omit refresh tokens depending on app settings/scopes.
            refresh_token = None

        self._persist_env_value('TWITTER_ACCESS_TOKEN', access_token)
        if refresh_token:
            self._persist_env_value('TWITTER_REFRESH_TOKEN', refresh_token)

        # Update in-memory values for this run
        self.access_token = access_token
        self.refresh_token = refresh_token
        return token

    def refresh_access_token(self) -> dict:
        """Refresh access token using the stored refresh token (requires offline.access + app settings)."""
        if self._is_missing_or_placeholder(self.refresh_token):
            raise ValueError("Missing TWITTER_REFRESH_TOKEN; cannot refresh.")

        assert isinstance(self.refresh_token, str)

        token = self._refresh_token(refresh_token=self.refresh_token)

        access_token = token.get('access_token')
        refresh_token = token.get('refresh_token') or self.refresh_token
        if self._is_missing_or_placeholder(access_token):
            raise Exception("Token refresh failed: no access_token returned.")

        assert access_token is not None

        self._persist_env_value('TWITTER_ACCESS_TOKEN', access_token)
        if refresh_token:
            self._persist_env_value('TWITTER_REFRESH_TOKEN', refresh_token)

        self.access_token = access_token
        self.refresh_token = refresh_token
        return token

    def _persist_env_value(self, key: str, value: str) -> None:
        if self._disable_persistence:
            return
        try:
            lines: list[str]
            if os.path.exists(self._env_path):
                with open(self._env_path, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
            else:
                lines = []

            updated = False
            new_lines: list[str] = []
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or '=' not in stripped:
                    new_lines.append(line)
                    continue
                existing_key = stripped.split('=', 1)[0].strip()
                if existing_key == key:
                    new_lines.append(f"{key}={value}")
                    updated = True
                else:
                    new_lines.append(line)

            if not updated:
                if new_lines and new_lines[-1].strip() != '':
                    new_lines.append('')
                new_lines.append(f"{key}={value}")

            with open(self._env_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(new_lines) + "\n")
        except Exception as e:
            raise Exception(f"Failed to update {self._env_path}: {str(e)}")
    
    def _authenticate(self):
        """Create a Tweepy client using an OAuth 2.0 *user* access token."""
        if self._is_missing_or_placeholder(self.access_token):
            raise ValueError(
                "Missing TWITTER_ACCESS_TOKEN. Run with --authorize to get the auth URL, "
                "then --callback-url to store tokens in .env."
            )

        try:
            # Use bearer_token with user_auth=False on requests.
            self.client = tweepy.Client(bearer_token=self.access_token)
            print("✓ Client initialized")
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def post_tweet(self, text):
        """
        Post a tweet using Twitter API v2
        
        Args:
            text (str): The tweet text to post (max 280 characters)
            
        Returns:
            dict: Response from Twitter API containing tweet data
        """
        if not text:
            raise ValueError("Tweet text cannot be empty")
        
        if len(text) > 280:
            raise ValueError(f"Tweet text too long ({len(text)} characters). Maximum is 280 characters.")

        if self.client is None:
            raise RuntimeError("Client is not initialized. Call _authenticate() first.")
        
        try:
            # Post tweet using API v2
            response = self.client.create_tweet(text=text, user_auth=False)
            print(f"✓ Tweet posted successfully!")
            response_data: Any = getattr(response, 'data', None) or {}
            tweet_id = response_data.get('id') if isinstance(response_data, dict) else None
            if tweet_id:
                print(f"  Tweet ID: {tweet_id}")
            print(f"  Text: {text}")
            return response_data
        except tweepy.TweepyException as e:
            message = str(e)
            # If Twitter rejects exact duplicates, retry once with a timestamp suffix.
            if 'duplicate content' in message.lower():
                suffix = datetime.now().strftime('%Y-%m-%d %H:%M')
                retry_text = f"{text} ({suffix})"
                response = self.client.create_tweet(text=retry_text, user_auth=False)
                response_data: Any = getattr(response, 'data', None) or {}
                tweet_id = response_data.get('id') if isinstance(response_data, dict) else None
                print("✓ Tweet posted successfully after dedupe")
                if tweet_id:
                    print(f"  Tweet ID: {tweet_id}")
                print(f"  Text: {retry_text}")
                return response_data

            raise Exception(f"Failed to post tweet: {message}")
    
    def verify_credentials(self):
        """
        Verify that the credentials are valid
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        try:
            if self.client is None:
                raise RuntimeError("Client is not initialized. Call _authenticate() first.")
            # Try to get authenticated user's information
            user = self.client.get_me(user_auth=False)
            user_data: Any = getattr(user, 'data', None)
            if user_data:
                username = getattr(user_data, 'username', None)
                if username:
                    print(f"✓ Credentials verified for user: @{username}")
                else:
                    print("✓ Credentials verified")
                return True
            return False
        except Exception as e:
            print(f"✗ Credential verification failed: {str(e)}")
            return False


def main():
    """Main function to run the Twitter bot"""
    print("=" * 50)
    print("Twitter Bot - Automated Posting")
    print("=" * 50)
    print()
    
    parser = argparse.ArgumentParser(description="Twitter Bot - Automated Posting")
    parser.add_argument(
        "--authorize",
        action="store_true",
        help="Print the OAuth authorization URL (visit it to authorize the app).",
    )
    parser.add_argument(
        "--callback-url",
        dest="callback_url",
        help="Exchange the full redirect URL for tokens and store them in .env.",
    )
    args = parser.parse_args()

    try:
        bot = TwitterBot()

        if args.authorize:
            auth_url = bot.get_authorization_url()
            print("\nOpen this URL in your browser and authorize the app:")
            print(auth_url)
            print("\nAfter authorization, copy the full redirect URL and run:")
            print("  python twitter_bot.py --callback-url '<PASTE_REDIRECT_URL_HERE>'")
            sys.exit(0)

        if args.callback_url:
            bot.exchange_callback_url_for_tokens(args.callback_url)
            print("\n✓ Tokens stored in .env")
            sys.exit(0)

        # Normal run: authenticate + verify + tweet
        bot._authenticate()

        print("\nVerifying credentials...")
        if not bot.verify_credentials():
            # Attempt refresh once if configured
            if not bot._is_missing_or_placeholder(bot.refresh_token):
                print("\nAttempting token refresh...")
                bot.refresh_access_token()
                bot._authenticate()
                if bot.verify_credentials():
                    pass
                else:
                    print("\n✗ Failed to verify credentials after refresh. Check your app permissions/scopes.")
                    sys.exit(1)
            else:
                print("\n✗ Failed to verify credentials. Please check your .env file.")
                sys.exit(1)

        tweet_message = bot.get_next_tweet_message()

        print("\nPosting tweet...")
        bot.post_tweet(tweet_message)

        print("\n" + "=" * 50)
        print("✓ Bot execution completed successfully!")
        print("=" * 50)

    except ValueError as e:
        print(f"\n✗ Configuration Error: {str(e)}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file")
        print("2. Set TWITTER_CLIENT_ID and REDIRECT_URI")
        print("3. Obtained TWITTER_ACCESS_TOKEN (run with --authorize / --callback-url)")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
