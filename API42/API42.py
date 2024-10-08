#!/usr/bin/python3
from typing import Any
import asyncio
import uuid
import time
import calendar
import os
import httpx
import uvicorn
import fastapi
from urllib.parse import urlparse, urlencode
import webbrowser

class API42:
	URL = "https://api.intra.42.fr"
	DELAY = 1
	def __init__(self, client_id: str, client_secret: str):
		self._client_id = client_id
		self._client_secret = client_secret
		self._lock = asyncio.Lock()
	async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
		loop = asyncio.get_event_loop()
		await self._lock.acquire()
		async with httpx.AsyncClient() as client:
			request = httpx.Request(method, self.URL + path, **kwargs)
			task = loop.create_task(client.send(request))
			loop.call_later(self.DELAY, self._lock.release)
			return await task
	async def client_credential(self) -> 'ClientCredential':
		return await ClientCredential.create(self)
	async def user_credential(self) -> 'UserCredential':
		return await UserCredential.create(self)

async def create_api42(client_id: str, client_secret: str, *, loop: asyncio.AbstractEventLoop = None) -> API42:
	return API42(client_id, client_secret, loop=loop)

class Credential:
	def __init__(self, api: API42, access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int):
		self._api = api
		self._access_token = access_token
		self._token_type = token_type
		self._expires_in = expires_in
		self._scope = scope
		self._created_at = created_at
		self._secret_valid_until = secret_valid_until
	async def _refresh(self) -> None:
		raise NotImplementedError
	async def _get_token(self) -> str:
		if time.time() >= self._created_at + self._expires_in:
			await self._refresh()
		return f"{self._token_type} {self._access_token}"
	async def _request(self, method: str, path: str, headers:dict = {}, **kwargs) -> httpx.Response:
		headers["Authorization"] = await self._get_token()
		return await self._api.request(method, path, headers=headers, **kwargs)
	async def request(self, method: str, path: str, **kwargs) -> Any:
		return (await self._request(method, path, **kwargs)).json()
	async def get(self, path: str, query: dict = {}) -> Any:
		return await self.request("GET", path, params=query)

class ClientCredential(Credential):
	def __init__(self, api: API42, access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int):
		super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
	@classmethod
	async def create(cls, api: API42) -> 'ClientCredential':
		data = {
			"grant_type": "client_credentials",
			"client_id": api._client_id,
			"client_secret": api._client_secret,
		}
		return cls(api, **(await api.request("POST", "/oauth/token", data=data)).json())
	async def _refresh(self) -> None:
		tmp = await ClientCredential.create(self._api)
		self._access_token = tmp._access_token
		self._token_type = tmp._token_type
		self._expires_in = tmp._expires_in
		self._scope = tmp._scope
		self._created_at = tmp._created_at
		self._secret_valid_until = tmp._secret_valid_until

class UserCredential(Credential):
	def __init__(self, api: 'API42', access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int, refresh_token: str):
		super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
		self._refresh_token = refresh_token
	@staticmethod
	async def get_code(api:'API42', scope:str, host:str, port:int) -> str:
		app = fastapi.FastAPI()
		_state = str(uuid.uuid4())
		_code = asyncio.Future()
		@app.get("/")
		async def _(*, code: str, state: str):
			res = "<script>window.close();</script>"
			if state == _state:
				_code.set_result(code)
				res += "<h1>Success</h1>"
			else:
				_code.set_exception(Exception("Invalid state"))
				res += "<h1>Failed</h1>"
			return fastapi.Response(content=res, media_type="text/html")
		config = uvicorn.Config(app, host=host, port=port)
		server = uvicorn.Server(config)
		server_task = asyncio.create_task(server.serve())
		query = {
			"client_id": api._client_id,
			"redirect_uri": f"http://{host}:{port}/",
			"response_type": "code",
			"scope": scope,
			"state": _state,
			}
		url = urlparse(f"{api.URL}/oauth/authorize")._replace(query=urlencode(query)).geturl()
		print(url)
		webbrowser.open_new(url)
		try:
			code = await _code
		finally:
			server.should_exit = True
			await server_task
		return code
	@classmethod
	async def create(cls, api: 'API42', scope: str = "public projects profile elearning tig forum") -> 'UserCredential':
		host = "localhost"
		port = 4242
		data = {
			"grant_type": "authorization_code",
			"client_id": api._client_id,
			"client_secret": api._client_secret,
			"code": await cls.get_code(api, scope, host, port),
			"redirect_uri": f"http://{host}:{port}/",
		}
		return cls(api, **(await api.request("POST", "/oauth/token", data=data)).json())
	async def _refresh(self) -> None:
		data = {
			"grant_type": "refresh_token",
			"refresh_token": self._refresh_token,
		}
		tmp = await self._api.request("POST", "/oauth/token", data=data)
		self._access_token = tmp["access_token"]
		self._token_type = tmp["token_type"]
		self._expires_in = tmp["expires_in"]
		self._scope = tmp["scope"]
		self._created_at = tmp["created_at"]
		self._secret_valid_until = tmp["secret_valid_until"]
		self._refresh_token = tmp["refresh_token"]
	async def me(self) -> dict:
		return await self.get("/v2/me")

async def make_api_flow(client_id:str=None, client_secret:str=None) -> API42:
	if client_id is None or client_secret is None:
		client_id = os.getenv("API42_CLIENT_ID")
		client_secret = os.getenv("API42_CLIENT_SECRET")
	if client_id is None or client_secret is None:
		while True:
			try:
				client_id = input("Client ID: ")
				break
			except KeyboardInterrupt:
				print()
		while True:
			try:
				client_secret = input("Client Secret: ")
				break
			except KeyboardInterrupt:
				print()
	return API42(client_id, client_secret)
