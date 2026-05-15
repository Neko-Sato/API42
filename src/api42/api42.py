#!/usr/bin/env python3
import asyncio
from authlib.integrations.httpx_client import AsyncOAuth2Client
import httpx
from urllib.parse import urljoin
from .auth import get_authorization_code
from .constants import SCOPES


class API42Client(AsyncOAuth2Client):
    URL = "https://api.intra.42.fr/"
    CONCURRENCY = 5
    DELAY = 2

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: set[str] | None = None,
        update_token=None,
    ):
        self.sem = asyncio.Semaphore(self.CONCURRENCY)
        if scope is not None:
            scope = scope & SCOPES
        AsyncOAuth2Client.__init__(
            self,
            base_url=self.URL,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_endpoint="/oauth/token",
            update_token=update_token,
            scope=scope,
        )

    def create_authorization_url(self) -> tuple[str, str]:
        uri, state = super().create_authorization_url("/oauth/authorize")
        uri = urljoin(self.URL, uri)
        return uri, state

    async def get_authorization_code(self) -> str:
        uri, state = self.create_authorization_url()
        return await get_authorization_code(uri, state, self.redirect_uri)

    async def fetch_token(self) -> dict:
        return await super().fetch_token()

    async def fetch_token_with_auth_flow(self) -> dict:
        code = await self.get_authorization_code()
        token = await super().fetch_token(code=code)
        return token

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
