#!/usr/bin/env python3
import asyncio
import json
from authlib.integrations.httpx_client import AsyncOAuth2Client
import httpx
from urllib.parse import urljoin
from pathlib import Path
from .auth import get_authorization_code


class API42Client(AsyncOAuth2Client):
    URL = "https://api.intra.42.fr/"
    CONCURRENCY = 5
    DELAY = 2

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        self.sem = asyncio.Semaphore(self.CONCURRENCY)
        AsyncOAuth2Client.__init__(
            self,
            base_url=self.URL,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_endpoint="/oauth/token",
            update_token=self._update_token,
        )

    async def _update_token(self, token, refresh_token=None, access_token=None):
        pass

    async def send(self, *args, **kwds) -> httpx.Response:
        async with self.sem:
            while True:
                try:
                    res = await super().send(*args, **kwds)
                    if res.status_code == 429:
                        await asyncio.sleep(self.DELAY)
                        continue
                    return res
                except httpx.TimeoutException:
                    await asyncio.sleep(self.DELAY)

    @classmethod
    async def create(cls, client_id: str, client_secret: str):
        client = cls(client_id, client_secret, None)
        await client.fetch_token()
        return client


class UserAPI42Client(API42Client):
    SCOPES = {"public", "projects", "profile", "elearning", "tig", "forum"}
    TOKEN_PATH = Path("~/.api42/token.json").expanduser()

    async def _update_token(self, token, refresh_token=None, access_token=None):
        self.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.TOKEN_PATH, "w") as f:
            json.dump(token, f)

    @classmethod
    async def create(cls, client_id: str, client_secret: str, redirect_uri: str, scope: set[str] = {"public"}):
        client = cls(client_id, client_secret, redirect_uri)
        scope = scope & cls.SCOPES
        if cls.TOKEN_PATH.exists():
            with open(cls.TOKEN_PATH, "r") as f:
                token = json.load(f)
            if set(token["scope"].split(" ")) >= scope:
                client.token = token
                try:
                    await client.refresh_token()
                    return client
                except:
                    pass
        uri, state = client.create_authorization_url(
            "/oauth/authorize", scope=" ".join(scope))
        uri = urljoin(cls.URL, uri)
        token = await client.fetch_token(
            grant_type="authorization_code",
            code=await get_authorization_code(uri, state, redirect_uri),
        )
        await client._update_token(token)
        return client
