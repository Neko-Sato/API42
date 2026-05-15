#!/usr/bin/env python3
from urllib.parse import urlunparse, urlparse, parse_qs
import getpass
from bs4 import BeautifulSoup, Tag
import httpx
from urllib.parse import urlparse, parse_qs


class SignInError(Exception):
    pass


async def get_authorization_code(url: str, state: str, redirect_uri: str) -> str:
    INFO = {
        "username": lambda: input("Username: "),
        "password": lambda: getpass.getpass("Password: "),
        "otp": lambda: input("OTP: "),
    }
    parsed_redirect_uri = urlparse(redirect_uri)

    def _is_redirect_uri(url: str) -> bool:
        tmp = urlparse(url)
        return tmp.scheme == parsed_redirect_uri.scheme \
            and tmp.netloc == parsed_redirect_uri.netloc \
            and tmp.path == parsed_redirect_uri.path
    while True:
        try:
            async with httpx.AsyncClient() as client:
                res: httpx.Response = await client.get(url, follow_redirects=True)
                res.raise_for_status()
                while True:
                    soup: Tag = BeautifulSoup(res.text, "html.parser")
                    form: Tag = soup.find("form")
                    if not form:
                        raise RuntimeError("hasn't got login form")
                    param = {}
                    for i in form.find_all("input", type=["text", "password", "hidden"]):
                        i: Tag
                        if i.attrs["type"] == "hidden":
                            if "value" in i.attrs:
                                param[i.attrs["name"]] = i.attrs["value"]
                        else:
                            if i.attrs["name"] in INFO:
                                param[i.attrs["name"]] = INFO[i.attrs["name"]]()
                            else:
                                raise SignInError()
                    res = await client.request(form.attrs["method"], form.attrs["action"], data=param, follow_redirects=False)
                    if res.is_redirect:
                        break
                    res.raise_for_status()
                while True:
                    url = res.headers["Location"]
                    if _is_redirect_uri(url):
                        query = parse_qs(urlparse(url).query)
                        if "code" in query and "state" in query:
                            if query["state"][0] != state:
                                raise RuntimeError("state mismatch")
                            return query["code"][0]
                    res = await client.get(url, follow_redirects=False)
                    if res.is_redirect:
                        continue
                    res.raise_for_status()
                    soup: Tag = BeautifulSoup(res.text, "html.parser")
                    form: Tag = soup.find(
                        "input", type="submit", value="Authorize")
                    if form is not None:
                        form: Tag = form.find_parent("form")
                    if form is None:
                        print(res.text)
                        raise RuntimeError("Incorrect redirect_uri or scope")
                    param = {}
                    for i in form.find_all("input", type=["hidden", "submit"]):
                        i: Tag
                        if "value" in i.attrs:
                            param[i.attrs["name"]] = i.attrs["value"]
                    url = urlunparse((res.url.scheme, res.url.host,
                                      form.attrs["action"], "", "", ""))
                    res = await client.request(form.attrs["method"], url, data=param, follow_redirects=False)
                    if res.is_redirect:
                        continue
                    res.raise_for_status()
                    raise RuntimeError("Unknown error")
        except SignInError:
            print("retry...")
