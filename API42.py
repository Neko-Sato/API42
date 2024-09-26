#!/usr/bin/python3
import asyncio
import httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, urlencode
import uuid
import time
import calendar

class Credential:
    def __init__(self, api: 'API42', access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int):
        self.api = api
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.scope = scope
        self.created_at = created_at
        self.secret_valid_until = secret_valid_until

    async def _refresh(self) -> None:
        raise NotImplementedError

    async def _get_token(self) -> str:
        if time.time() >= self.created_at + self.expires_in:
            await self._refresh()
        return f"{self.token_type} {self.access_token}"

    async def get_pisciners(self, campus: int, year: int, month: int) -> dict:
        query = {"campus_id": campus, "filter[pool_month]": calendar.month_name[month].lower(), "filter[pool_year]": year, "page[size]": 100}
        users = {}
        i = 1
        while True:
            tmp = {u["id"]: u["login"] for u in await self.get("/v2/users", {**query, "page[number]": i})}
            users.update(tmp)
            if len(tmp) < 100:
                break
            i += 1
        return users

    async def get(self, path: str, query: dict = {}) -> dict:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": await self._get_token(),
            }
            response = await client.get(f"{self.api.URL}{path}", headers=headers, params=query)
            return response.json()

class ClientCredential(Credential):
    def __init__(self, api: 'API42', access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int):
        super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)

    @staticmethod
    async def create(api: 'API42') -> 'ClientCredential':
        data = {
            "grant_type": "client_credentials",
            "client_id": api.client_id,
            "client_secret": api.client_secret,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api.URL}/oauth/token", data=data)
            return ClientCredential(api, **response.json())

    async def _refresh(self) -> None:
        tmp = await ClientCredential.create(self.api)
        self.access_token = tmp.access_token
        self.token_type = tmp.token_type
        self.expires_in = tmp.expires_in
        self.scope = tmp.scope
        self.created_at = tmp.created_at
        self.secret_valid_until = tmp.secret_valid_until

class UserCredential(Credential):
    def __init__(self, api: 'API42', access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int, refresh_token: str):
        super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
        self.refresh_token = refresh_token

    @staticmethod
    async def create(api: 'API42', scope: str = "public projects profile elearning tig forum") -> 'UserCredential':
        host = "localhost"
        port = 4242
        _state = str(uuid.uuid4())
        _code = asyncio.Future()

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = urlparse(self.path)
                state = query.query.split("&")[0].split("=")[1] if "state" in query.query else None
                code = query.query.split("&")[1].split("=")[1] if "code" in query.query else None
                if code and _state == state:
                    _code.set_result(code)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<script>window.close();</script>Sign In...")
                else:
                    _code.set_exception(Exception())
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"error")

        server = HTTPServer((host, port), RequestHandler)
        url = urlparse(f"{api.URL}/oauth/authorize")
        query = {
            "client_id": api.client_id,
            "redirect_uri": f"http://{host}:{port}/",
            "response_type": "code",
            "scope": scope,
            "state": _state,
        }
        url = url._replace(query=urlencode(query)).geturl()
        print(url)

        try:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, server.serve_forever)
            code = await _code
        finally:
            server.shutdown()
            server.server_close()

        data = {
            "grant_type": "authorization_code",
            "client_id": api.client_id,
            "client_secret": api.client_secret,
            "code": code,
            "redirect_uri": f"http://{host}:{port}/",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api.URL}/oauth/token", data=data)
            return UserCredential(api, **response.json())

    async def _refresh(self) -> None:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api.URL}/oauth/token", data=data)
            tmp = response.json()
            self.access_token = tmp["access_token"]
            self.token_type = tmp["token_type"]
            self.expires_in = tmp["expires_in"]
            self.scope = tmp["scope"]
            self.created_at = tmp["created_at"]
            self.secret_valid_until = tmp["secret_valid_until"]
            self.refresh_token = tmp["refresh_token"]

    async def me(self) -> dict:
        return await self.get("/v2/me")

class API42:
    URL = "https://api.intra.42.fr"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def client_credential(self) -> ClientCredential:
        return await ClientCredential.create(self)

    async def user_credential(self, scope: str = "public projects profile elearning tig forum") -> UserCredential:
        return await UserCredential.create(self, scope)
