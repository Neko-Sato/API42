#!/usr/bin/python3
import asyncio
import uuid
from urllib.parse import urlunparse, urlparse, urlencode, parse_qs
import httpx
import getpass
from bs4 import BeautifulSoup, Tag

class AUTH42:
	URL = "https://api.intra.42.fr"
	def __init__(self, client_id:str, redirect_uri:str, scope:str):
		self._client_id = client_id
		self._redirect_uri = redirect_uri
		self._scope = scope
	def get_authorize_url(self, state:str) -> str:
		query:dict[str, str] = {
			"client_id": self._client_id,
			"redirect_uri": self._redirect_uri,
			"response_type": "code",
			"scope": self._scope,
			"state": state,
			}
		return urlparse(f"{self.URL}/oauth/authorize")._replace(query=urlencode(query)).geturl()
	def _is_redirect_uri(self, url:str) -> bool:
		tmp = urlparse(url)
		tmp2 = urlparse(self._redirect_uri)
		return tmp.scheme == tmp2.scheme and tmp.netloc == tmp2.netloc and tmp.path == tmp2.path
	async def signin(self, username:str, password:str, otp:None|str=None) -> str:
		info = {"username": username, "password": password, "otp": otp}
		state:str = str(uuid.uuid4())
		url:str = self.get_authorize_url(state)
		async with httpx.AsyncClient() as client:
			res:httpx.Response = await client.get(url, follow_redirects=True)
			if res.status_code != 200:
				raise Exception("Failed to signin (hasn't got login page)")
			while True:
				soup:Tag = BeautifulSoup(res.text, "html.parser")
				form:Tag = soup.find("form")
				if not form:
					raise Exception("Failed to signin (hasn't got login form)")
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
							raise Exception(f"Failed to signin (missing {i.attrs['name']})")
				res = await client.request(form.attrs["method"], form.attrs["action"], data=param, follow_redirects=False)
				if res.status_code == 302:
					break
				elif res.status_code != 200:
					raise Exception("Failed to signin (failed to login)")
			while True:
				url = res.headers["Location"]
				if self._is_redirect_uri(url):
					query = parse_qs(urlparse(url).query)
					if "code" in query and "state" in query:
						if query["state"][0] != state:
							raise Exception("Failed to signin (state mismatch)")
						return query["code"][0]
				res = await client.get(url, follow_redirects=False)
				if res.status_code == 200:
					soup:Tag = BeautifulSoup(res.text, "html.parser")
					form:Tag = soup.find("input", type="submit", value="Authorize")
					if not form:
						raise Exception("Failed to signin (hasn't got authorize form)")
					form:Tag = form.find_parent("form")
					if not form:
						raise Exception("Failed to signin (hasn't got authorize form)")
					param = {}
					for i in form.find_all("input", type=["hidden", "submit"]):
						i:Tag
						if "value" in i.attrs:
							param[i.attrs["name"]] = i.attrs["value"]
					url = urlunparse((res.url.scheme, res.url.host, form.attrs["action"], "", "", ""))
					res = await client.request(form.attrs["method"], url, data=param, follow_redirects=False)
					if res.status_code != 302:
						raise Exception("Failed to signin (failed to authorize)")
				elif res.status_code != 302:
					raise Exception("Failed to signin (failed to authorize)")

async def signin_flow(client_id:str, redirect_uri:str, scope:str="public") -> str:
	auth = AUTH42(client_id, redirect_uri, scope)
	username = input("username: ")
	password = getpass.getpass("password: ")
	otp = input("otp: ")
	return await auth.signin(username, password, otp)

async def main(client_id:str, redirect_uri:str, scope:str) -> None:
	try:
		code = await signin_flow(client_id, redirect_uri, scope)
		print(f"code: {code}")
		return 0
	except Exception as e:
		print(e)
		return 1

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("client_id", type=str, default=None)
	parser.add_argument("redirect_uri", type=str, default="http://localhost:4242")
	parser.add_argument('--scope', nargs='+', default=["public"])

	args = parser.parse_args()
	exit(asyncio.run(main(args.client_id, args.redirect_uri, " ".join(args.scope))))
