#!/usr/bin/python3
import asyncio
import uuid
from urllib.parse import urlunparse, urlparse, urlencode, parse_qs
import httpx
import getpass
from bs4 import BeautifulSoup, Tag

class SignInError(Exception):
	pass

class InvalidCredentials(SignInError):
	pass

class AUTH42:
	URL = "https://api.intra.42.fr"
	SCOPES = ["public", "projects", "profile", "elerning", "tig", "forum"]	
	def __init__(self, client_id:str, redirect_uri:str, *, scope:list[str]|None=None):
		self._client_id = client_id
		self._redirect_uri = redirect_uri
		self._scope = scope
	def get_authorize_url(self, state:str) -> str:
		query:dict[str, str] = {}
		query["client_id"] = self._client_id
		query["redirect_uri"] = self._redirect_uri
		query["response_type"] = "code"
		query["state"] = state
		if self._scope is not None:
			query["scope"] = " ".join(self._scope)
		return urlparse(f"{self.URL}/oauth/authorize")._replace(query=urlencode(query)).geturl()
	def _is_redirect_uri(self, url:str) -> bool:
		tmp = urlparse(url)
		tmp2 = urlparse(self._redirect_uri)
		return tmp.scheme == tmp2.scheme and tmp.netloc == tmp2.netloc and tmp.path == tmp2.path
	async def signin(self, username:str, password:str, *, otp:str|None=None) -> str:
		info = {"username": username, "password": password, "otp": otp}
		state:str = str(uuid.uuid4())
		url:str = self.get_authorize_url(state)
		async with httpx.AsyncClient() as client:
			res:httpx.Response = await client.get(url, follow_redirects=True)
			if res.status_code != 200:
				raise SignInError("hasn't got login page")
			while True:
				soup:Tag = BeautifulSoup(res.text, "html.parser")
				form:Tag = soup.find("form")
				if not form:
					raise SignInError("hasn't got login form")
				param = {}
				for i in form.find_all("input", type=["text", "password", "hidden"]):
					i:Tag
					if i.attrs["type"] == "hidden":
						if "value" in i.attrs:
							param[i.attrs["name"]] = i.attrs["value"]
					else:
						if i.attrs["name"] in info:
							param[i.attrs["name"]] = info.pop(i.attrs["name"])
						else:
							raise InvalidCredentials()
				res = await client.request(form.attrs["method"], form.attrs["action"], data=param, follow_redirects=False)
				if res.status_code == 302:
					break
				elif res.status_code != 200:
					raise SignInError("failed to login")
			while True:
				url = res.headers["Location"]
				if self._is_redirect_uri(url):
					query = parse_qs(urlparse(url).query)
					if "code" in query and "state" in query:
						if query["state"][0] != state:
							raise SignInError("state mismatch")
						return query["code"][0]
				res = await client.get(url, follow_redirects=False)
				if res.status_code == 200:
					soup:Tag = BeautifulSoup(res.text, "html.parser")
					form:Tag = soup.find("input", type="submit", value="Authorize")
					if form:
						form:Tag = form.find_parent("form")
					if not form:
						raise SignInError("hasn't got authorize form")
					param = {}
					for i in form.find_all("input", type=["hidden", "submit"]):
						i:Tag
						if "value" in i.attrs:
							param[i.attrs["name"]] = i.attrs["value"]
					url = urlunparse((res.url.scheme, res.url.host, form.attrs["action"], "", "", ""))
					res = await client.request(form.attrs["method"], url, data=param, follow_redirects=False)
					if res.status_code != 302:
						raise SignInError("failed to authorize")
				elif res.status_code != 302:
					raise SignInError("failed to redirect")

async def main(client_id, redirect_uri, scope) -> int:
	auth = AUTH42(client_id, redirect_uri, scope=scope)
	username = input("Username: ")
	password = getpass.getpass("Password: ")
	otp = input("OTP: ") or None
	try:
		code = await auth.signin(username, password, otp=otp)
		print(f"Code: {code}")
		return 0
	except Exception as e:
		print(e)
		return 1
	
if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser()
	parser.add_argument("client_id", type=str)
	parser.add_argument("redirect_uri", type=str)
	parser.add_argument("--scope", type=str, nargs="+")
	args = parser.parse_args()

	exit(asyncio.run(main(args.client_id, args.redirect_uri, args.scope)))
