#!/usr/bin/python3
import asyncio
import time
import httpx
import json
from .AUTH42 import AUTH42

JsonType = dict[str, "JsonType"] | list["JsonType"] | str | int | float | bool | None

class API42:
	URL = "https://api.intra.42.fr"
	Delay = 1
	Retry = 10
	def __init__(self, client_id: str, client_secret: str):
		self._client_id:str = client_id
		self._client_secret:str = client_secret
		self._lock:asyncio.Lock = asyncio.Lock()
	async def _request(self, method:str, path:str, **kwds) -> httpx.Response:
		async with self._lock:
			async with httpx.AsyncClient() as client:
				count = 0
				while True:
					try:
						return await client.request(method, f"{self.URL}{path}", **kwds)
					except httpx.TimeoutException:
						if count >= self.Retry:
							raise
						await asyncio.sleep(self.Delay)
						count += 1
	async def request(self, credential:'Credential', method:str, path:str, headers:dict={}, **kwds) -> httpx.Response:
		if credential.need_refresh():
			await credential.refresh(self)
		headers["Authorization"] = f"{credential._token_type} {credential._access_token}"
		return await self._request(method, path, headers=headers, **kwds)
	async def get(self, credential:'Credential', path:str, query:dict={}) -> JsonType:
		return (await self.request(credential, "GET", path, params=query)).json()
						
class Credential:
	def __init__(self, **kwds):
		self._access_token:str = kwds["access_token"]
		self._token_type:str = kwds["token_type"]
		self._expires_in:int = kwds["expires_in"]
		self._scope:str = kwds["scope"]
		self._created_at:int = kwds["created_at"]
		self._secret_valid_until:int = kwds["secret_valid_until"]
	async def refresh(self, api: API42) -> None:
		...
	def need_refresh(self) -> bool:
		return self._secret_valid_until - 180 < time.time()

class ClientCredential(Credential):
	@staticmethod
	async def _generate(api: API42) -> dict:
		data = {
			"grant_type": "client_credentials",
			"client_id": api._client_id,
			"client_secret": api._client_secret,
		}
		res = await api._request("POST", "/oauth/token", data=data)
		return res.json()
	@staticmethod
	async def create(api: API42) -> 'ClientCredential':
		return ClientCredential(**(await ClientCredential._generate(api)))
	async def refresh(self, api: API42) -> None:
		tmp = await self._generate(api)
		self._access_token = tmp["access_token"]
		self._token_type = tmp["token_type"]
		self._expires_in = tmp["expires_in"]
		self._scope = tmp["scope"]
		self._created_at = tmp["created_at"]
		self._secret_valid_until = tmp["secret_valid_until"]

class ReSignInRequiredError(Exception):
	pass

class UserCredential(ClientCredential):
	def __init__(self, **kwds):
		super().__init__(**kwds)
		self._refresh_token:str = kwds["refresh_token"]
		self
	@staticmethod
	async def create(api: 'API42', redirect_uri:str, username:str, password:str, *,
			scope:list[str]|None=None, otp:None|str=None) -> 'UserCredential':
		auth = AUTH42(api._client_id, redirect_uri, scope=scope)
		data = {
			"grant_type": "authorization_code",
			"client_id": api._client_id,
			"client_secret": api._client_secret,
			"code": await auth.signin(username, password, otp=otp),
			"redirect_uri": redirect_uri,
		}
		res = await api._request("POST", "/oauth/token", data=data)
		return UserCredential(**res.json())
	async def refresh(self, api: API42) -> None:
		data = {
			"grant_type": "refresh_token",
			"refresh_token": self._refresh_token,
		}
		res = await api._request("POST", "/oauth/token", data=data)
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
		self.save(api)
	def save(self, filename:str) -> None:
		with open(filename, "w", encoding="ascii") as f:
			data = {
				"access_token": self._access_token,
				"token_type": self._token_type,
				"expires_in": self._expires_in,
				"scope": self._scope,
				"created_at": self._created_at,
				"secret_valid_until": self._secret_valid_until,
				"refresh_token": self._refresh_token,
			}
			json.dump(data, f)
	@staticmethod
	async def load(api:API42, filename:str) -> 'UserCredential':
		with open(filename, "r", encoding="ascii") as f:
			data = json.load(f)
		credential = UserCredential(**data)
		await credential.refresh(api)
		return credential
