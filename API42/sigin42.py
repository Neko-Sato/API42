#!/usr/bin/python3
import asyncio
import uuid
from urllib.parse import urlunparse, urlparse, urlencode, parse_qs
import httpx
from bs4 import BeautifulSoup, Tag
import getpass

URL = "https://api.intra.42.fr"

def _check_url(url:str, redirect_uri:str) -> bool:
	tmp = urlparse(url)
	tmp2 = urlparse(redirect_uri)
	return tmp.scheme == tmp2.scheme and tmp.netloc == tmp2.netloc and tmp.path == tmp2.path

async def signin_flow(client_id:str, redirect_uri:str, scope:str) -> str:
	_state:str = str(uuid.uuid4())
	query:dict[str, str] = {
		"client_id": client_id,
		"redirect_uri": redirect_uri,
		"response_type": "code",
		"scope": scope,
		"state": _state,
		}
	url:str = urlparse(f"{URL}/oauth/authorize")._replace(query=urlencode(query)).geturl()
	async with httpx.AsyncClient() as client:
		res:httpx.Response = await client.get(url, follow_redirects=True)
		if res.status_code != 200:
			raise Exception("Failed to signin")
		while True:
			soup:Tag = BeautifulSoup(res.text, "html.parser")
			form:Tag = soup.find("form")
			if not form:
				raise Exception("Failed to signin")
			param = {}
			for i in form.find_all("input", type=["text", "password", "hidden"]):
				i:Tag
				if i.attrs["type"] == "hidden":
					if "value" in i.attrs:
						param[i.attrs["name"]] = i.attrs["value"]
				elif i.attrs["type"] == "password":
					param[i.attrs["name"]] = getpass.getpass(f"{i.attrs['name']}: ")
				else:
					param[i.attrs["name"]] = input(f"{i.attrs['name']}: ")
			res = await client.request(form.attrs["method"], form.attrs["action"], data=param, follow_redirects=False)
			if res.status_code == 302:
				break
			elif res.status_code != 200:
				raise Exception("Failed to signin")
		while True:
			url = res.headers["Location"]
			if _check_url(url, redirect_uri):
				query = parse_qs(urlparse(url).query)
				if "code" in query and "state" in query:
					if query["state"][0] != _state:
						raise Exception("Failed to signin")
					return query["code"][0]
			res = await client.get(url, follow_redirects=False)
			if res.status_code == 200:
				soup:Tag = BeautifulSoup(res.text, "html.parser")
				form:Tag = soup.find("input", type="submit", value="Authorize")
				if not form:
					raise Exception("Failed to signin")
				form:Tag = form.find_parent("form")
				if not form:
					raise Exception("Failed to signin")
				param = {}
				for i in form.find_all("input", type=["hidden", "submit"]):
					i:Tag
					if "value" in i.attrs:
						param[i.attrs["name"]] = i.attrs["value"]
				url = urlunparse((res.url.scheme, res.url.host, form.attrs["action"], "", "", ""))
				res = await client.request(form.attrs["method"], url, data=param, follow_redirects=False)
				if res.status_code != 302:
					raise Exception("Failed to signin")
			elif res.status_code != 302:
				raise Exception("Failed to signin")

async def main(client_id:str, redirect_uri:str, scope:str) -> int:
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
