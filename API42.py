import asyncio
from aiohttp import web, ClientSession
from urllib.parse import urlparse, urlencode
import uuid
import webbrowser

class Credential:
	def __init__(self, api:'API42', access_token:str, token_type:str, expires_in:int, scope:str, created_at:int, secret_valid_until:int):
		self.api = api
		self.access_token = access_token
		self.token_type = token_type
		self.expires_in = expires_in
		self.scope = scope
		self.created_at = created_at
		self.secret_valid_until = secret_valid_until
	async def refresh(self) -> None:
		raise NotImplementedError
	async def get_toekn(self) -> str:
		if self.created_at + self.expires_in >= self.secret_valid_until:
			await self.refresh()
		return f"{self.token_type} {self.access_token}"
	async def get(self, path:str, query:dict={}) -> dict:
		async with ClientSession() as session:
			headers = {
				"Authorization": await self.get_toekn(),
			}
			async with session.get(f"{self.api.URL}{path}", headers=headers, params=query) as response:
				return await response.json()

class ClientCredential(Credential):
	def __init__(self, api:'API42', access_token:str, token_type:str, expires_in:int, scope:str, created_at:int, secret_valid_until:int):
		super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
	@staticmethod
	async def create(api:'API42') -> 'ClientCredential':
		data = {
			"grant_type": "client_credentials",
			"client_id": api.client_id,
			"client_secret": api.client_secret,
		}
		async with ClientSession() as session:
			async with session.post(f"{api.URL}/oauth/token", data=data) as response:
				return ClientCredential(api, **(await response.json()))
	async def refresh(self) -> None:
		new = await ClientCredential.create(self.api)
		self.access_token = new.access_token
		self.token_type = new.token_type
		self.expires_in = new.expires_in
		self.scope = new.scope
		self.created_at = new.created_at
		self.secret_valid_until = new.secret_valid_until

class UserCredential(Credential):
	def __init__(self, api:'API42', access_token:str, token_type:str, expires_in:int, scope:str, created_at:int, secret_valid_until:int, refresh_token:str):
		super().__init__(api, access_token, token_type, expires_in, scope, created_at, secret_valid_until)
		self.refresh_token = refresh_token
	@staticmethod
	async def create(api:'API42', scope:str="public projects profile elearning tig forum") -> 'UserCredential':
		host = "localhost"
		port = 4242
		_state = str(uuid.uuid4())
		_code = asyncio.Future()
		app = web.Application()
		async def handler(request: web.Request) -> web.Response:
			state = request.query.get("state")
			code = request.query.get("code")
			if code and _state == state:
				_code.set_result(code)
				text = "Sign In..."
			else:
				_code.set_exception(Exception())
				text = "error"
			return web.Response(text=text)
		app.add_routes([web.get("/", handler)])
		server = asyncio.create_task(
			web._run_app(app=app, host=host, port=port))
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
		webbrowser.open_new(url)
		try:
			code = await _code
		finally:
			server.cancel()
		data = {
			"grant_type": "authorization_code",
			"client_id": api.client_id,
			"client_secret": api.client_secret,
			"code": code,
			"redirect_uri": f"http://{host}:{port}/",
		}
		async with ClientSession() as session:
			async with session.post(f"{api.URL}/oauth/token", data=data) as response:
				return UserCredential(api, **(await response.json()))
	async def refresh(self) -> None:
		data = {
			"grant_type": "refresh_token",
			"refresh_token": self.refresh_token,
		}
		async with ClientSession() as session:
			async with session.post(f"{self.api.URL}/oauth/token", data=data) as response:
				tmp = await response.json()
				self.access_token = tmp["access_token"]
				self.token_type = tmp["token_type"]
				self.expires_in = tmp["expires_in"]
				self.scope = tmp["scope"]
				self.created_at = tmp["created_at"]
				self.secret_valid_until = tmp["secret_valid_until"]
				self.refresh_token = tmp["refresh_token"]
	async def me(self) -> dict:
		async with ClientSession() as session:
			headers = {
				"Authorization": await self.get_toekn(),
			}
			async with session.get(f"{self.api.URL}/v2/me", headers=headers) as response:
				return await response.json()

class API42:
	URL = "https://api.intra.42.fr"
	def __init__(self, client_id:str, client_secret:str):
		self.client_id = client_id
		self.client_secret = client_secret
	async def client_credential(self) -> ClientCredential:
		return await ClientCredential.create(self)
	async def user_credential(self, scope:str="public projects profile elearning tig forum") -> UserCredential:
		return await UserCredential.create(self, scope)
