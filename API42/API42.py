#!/usr/bin/python3
import asyncio
import os
import time
import httpx
import json

JsonType = dict[str, "JsonType"] | list["JsonType"] | str | int | float | bool | None

class API42:
	URL = "https://api.intra.42.fr"
	DELAY = 1
	def __init__(self, client_id: str, client_secret: str):
		self._client_id = client_id
		self._client_secret = client_secret
		self._queue = asyncio.Queue()
		self._worker_task = asyncio.create_task(self._worker())
	def __del__(self):
		self._worker_task.cancel()
	async def _worker(self) -> None:
		try:
			async with httpx.AsyncClient() as client:
				request: httpx.Response
				future: asyncio.Future
				while True:
					request, future = await self._queue.get()
					try:
						future.set_result(await client.send(request))
					except httpx.ConnectTimeout:
						await self._queue.put((request, future))
					except Exception as e:
						future.set_exception(e)
					finally:
						await asyncio.sleep(self.DELAY)
		except asyncio.CancelledError:
			pass
	async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
		request = httpx.Request(method, self.URL + path, **kwargs)
		future = asyncio.Future()
		await self._queue.put((request, future))
		return await future
	async def client_credential(self) -> 'ClientCredential':
		return await ClientCredential.create(self)
	async def user_credential(self, code:str) -> 'UserCredential':
		return await UserCredential.create(self, code)

async def create_api42(client_id: str, client_secret: str, *, loop: asyncio.AbstractEventLoop = None) -> API42:
	return API42(client_id, client_secret, loop=loop)

class Credential:
	@staticmethod
	async def _get_token(api: API42) -> dict:
		raise NotImplementedError
	@classmethod
	async def create(cls, api: API42, *args, **kwds) -> 'ClientCredential':
		return cls(api, **(await cls._get_token(api, *args, **kwds)))
	def __init__(self, api: API42, access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int):
		self._api = api
		self._access_token = access_token
		self._token_type = token_type
		self._expires_in = expires_in
		self._scope = scope
		self._created_at = created_at
		self._secret_valid_until = secret_valid_until
	async def refresh(self) -> None:
		raise NotImplementedError
	async def _request(self, method: str, path: str, headers:dict = {}, **kwargs) -> httpx.Response:
		if self._secret_valid_until - 180 < time.time():
			await self.refresh()
		headers["Authorization"] = f"{self._token_type} {self._access_token}"
		return await self._api.request(method, path, headers=headers, **kwargs)
	async def request(self, method: str, path: str, **kwargs) -> JsonType:
		return (await self._request(method, path, **kwargs)).json()
	async def get(self, path: str, query: dict = {}) -> JsonType:
		return await self.request("GET", path, params=query)

class ClientCredential(Credential):
	def __init__(self, api: API42, access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int):
		super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
	@staticmethod
	async def _get_token(api: API42) -> dict:
		data = {
			"grant_type": "client_credentials",
			"client_id": api._client_id,
			"client_secret": api._client_secret,
		}
		return (await api.request("POST", "/oauth/token", data=data)).json()
	async def refresh(self) -> None:
		tmp = await self._get_token(self._api)
		self._access_token = tmp["access_token"]
		self._token_type = tmp["token_type"]
		self._expires_in = tmp["expires_in"]
		self._scope = tmp["scope"]
		self._created_at = tmp["created_at"]
		self._secret_valid_until = tmp["secret_valid_until"]

class ReSignInRequiredError(Exception):
	pass

class UserCredential(Credential):
	def __init__(self, api: 'API42', access_token: str, token_type: str, expires_in: int, scope: str, created_at: int, secret_valid_until: int, refresh_token: str):
		super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
		self._refresh_token = refresh_token
	@staticmethod
	async def _get_token(api: 'API42', code:str) -> dict:
		redirect_uri = "http://localhost:4242/"
		data = {
			"grant_type": "authorization_code",
			"client_id": api._client_id,
			"client_secret": api._client_secret,
			"code": code,
			"redirect_uri": redirect_uri,
		}
		return (await api.request("POST", "/oauth/token", data=data)).json()
	async def refresh(self) -> None:
		data = {
			"grant_type": "refresh_token",
			"refresh_token": self._refresh_token,
		}
		res = await self._api.request("POST", "/oauth/token", data=data)
		if res.status_code // 100 != 2:
			raise ReSignInRequiredError()
		tmp = res.json()
		self._access_token = tmp["access_token"]
		self._token_type = tmp["token_type"]
		self._expires_in = tmp["expires_in"]
		self._scope = tmp["scope"]
		self._created_at = tmp["created_at"]
		self._secret_valid_until = tmp["secret_valid_until"]
		self._refresh_token = tmp["refresh_token"]
	async def me(self) -> dict:
		return await self.get("/v2/me")
	def save(self, filename:str) -> None:
		data = {
			"access_token": self._access_token,
			"token_type": self._token_type,
			"expires_in": self._expires_in,
			"scope": self._scope,
			"created_at": self._created_at,
			"secret_valid_until": self._secret_valid_until,
			"refresh_token": self._refresh_token,
		}
		json.dump(data, open(filename, "bw"))
	@staticmethod
	def load(api:API42, filename:str) -> 'UserCredential':
		data = json.load(open(filename, "br"))
		return UserCredential(api, **data)

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
