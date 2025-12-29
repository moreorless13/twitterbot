from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from requests.auth import HTTPBasicAuth


@dataclass
class OAuth2PKCETokens:
    access_token: str
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    scope: str | None = None
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            'access_token': self.access_token,
        }
        if self.refresh_token is not None:
            out['refresh_token'] = self.refresh_token
        if self.token_type is not None:
            out['token_type'] = self.token_type
        if self.expires_in is not None:
            out['expires_in'] = self.expires_in
        if self.scope is not None:
            out['scope'] = self.scope
        if self.raw is not None:
            out['_raw'] = self.raw
        return out


class OAuth2PKCEAuth:
    """OAuth 2.0 Authorization Code + PKCE helper for X (Twitter).

    Interface intentionally mirrors the sample from the X developer platform:
    - get_authorization_url()
    - fetch_token(authorization_response=<full redirect URL>)

    Notes:
    - This implementation is for public/PKCE clients (no client_secret in token call).
    - If your X app is configured as a confidential client, you can still add Basic auth,
      but PKCE user-context apps typically operate as public clients.
    """

    authorize_url = 'https://twitter.com/i/oauth2/authorize'
    token_url = 'https://api.twitter.com/2/oauth2/token'

    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str,
        *,
        client_secret: str | None = None,
        client_auth: str = 'auto',
        timeout_seconds: int = 30,
    ) -> None:
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.timeout_seconds = timeout_seconds

        self.client_secret = client_secret
        # 'auto' (default): use Basic if client_secret is present, otherwise public.
        # 'basic': always use Basic (requires client_secret).
        # 'none': never use Basic (public PKCE client).
        self.client_auth = client_auth.strip().lower() if client_auth else 'auto'

        self.code_verifier: str | None = None
        self.state: str | None = None

    @staticmethod
    def _b64url_no_pad(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')

    @classmethod
    def _code_challenge_s256(cls, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode('ascii')).digest()
        return cls._b64url_no_pad(digest)

    def _ensure_pkce(self) -> None:
        if not self.code_verifier:
            # RFC 7636: verifier length 43-128. Use a URL-safe random string.
            self.code_verifier = secrets.token_urlsafe(64)[:128]
        if not self.state:
            self.state = secrets.token_urlsafe(24)

    def get_authorization_url(self) -> str:
        self._ensure_pkce()
        assert self.code_verifier is not None
        assert self.state is not None

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': self.state,
            'code_challenge': self._code_challenge_s256(self.code_verifier),
            'code_challenge_method': 'S256',
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    def _basic_auth(self) -> HTTPBasicAuth | None:
        mode = self.client_auth
        if mode not in {'auto', 'basic', 'none'}:
            mode = 'auto'

        if mode == 'none':
            return None

        if mode == 'basic':
            if not self.client_secret:
                raise ValueError('client_auth=basic requires client_secret')
            return HTTPBasicAuth(self.client_id, self.client_secret)

        # auto
        if not self.client_secret:
            return None
        return HTTPBasicAuth(self.client_id, self.client_secret)

    @staticmethod
    def _looks_like_missing_auth_header(resp: requests.Response) -> bool:
        text = (resp.text or '').lower()
        return (
            resp.status_code in {400, 401}
            and (
                'missing valid authorization header' in text
                or 'authorization header' in text
                or 'unauthorized_client' in text
                or 'invalid_client' in text
            )
        )

    def fetch_token(self, *, authorization_response: str) -> dict[str, Any]:
        """Exchange the redirect/callback URL for tokens.

        Returns a dict compatible with the sample usage:
        tokens["access_token"], tokens["refresh_token"], etc.
        """
        parsed = urlparse(authorization_response)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError('authorization_response must be a full URL (including scheme and host)')

        query = parse_qs(parsed.query)
        code = (query.get('code') or [None])[0]
        returned_state = (query.get('state') or [None])[0]
        if not code:
            raise ValueError('authorization_response is missing required query parameter: code')

        self._ensure_pkce()
        assert self.code_verifier is not None
        assert self.state is not None

        if returned_state and returned_state != self.state:
            raise ValueError('State mismatch. Re-run authorization and use the new redirect URL.')

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': self.code_verifier,
        }

        auth = self._basic_auth()
        resp = requests.post(
            self.token_url,
            headers=headers,
            data=data,
            auth=auth,
            timeout=self.timeout_seconds,
        )

        # If the app is configured as a confidential client, Twitter will demand Basic auth.
        # In auto/none modes, retry with Basic auth if we have a client_secret.
        if auth is None and self.client_secret and self._looks_like_missing_auth_header(resp):
            resp = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                timeout=self.timeout_seconds,
            )

        # If we tried Basic auth but Twitter behaves like a public PKCE client, retry without auth.
        if auth is not None and self._looks_like_missing_auth_header(resp):
            resp = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                auth=None,
                timeout=self.timeout_seconds,
            )
        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except Exception:
                payload = None

            err = None
            desc = None
            if isinstance(payload, dict):
                err = payload.get('error')
                desc = payload.get('error_description') or payload.get('detail')

            body = resp.text.strip()
            if len(body) > 800:
                body = body[:800] + '…'

            extra = ''
            if err or desc:
                extra = f" error={err!s} desc={desc!s}".rstrip()

            raise Exception(f"Token exchange failed (HTTP {resp.status_code}).{extra} body={body}")

        token: dict[str, Any] = resp.json()
        return token
