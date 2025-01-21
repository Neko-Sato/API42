#!/usr/bin/python3
import os
from API42 import API42, UserCredential, SignInError
import getpass

def make_api_flow(client_id:str|None=None, client_secret:str|None=None) -> API42:
	if client_id is None or client_secret is None:
		client_id = os.getenv("API42_CLIENT_ID", None)
		client_secret = os.getenv("API42_CLIENT_SECRET", None)
	if client_id is None or client_secret is None:
		if client_id is None:
			input("client_id: ")
		if client_secret is None:
			input("client_secret: ")
	return API42(client_id, client_secret)

async def make_user_credential(api: API42, redirect_uri:str|None=None, *, scope: set[str]={}) -> UserCredential:
	if redirect_uri is None:
		redirect_uri = os.getenv("API42_REDIRECT_URI", None)
	if redirect_uri is None:
		input("redirect_uri: ")
	while True:
		try:
			username = input("Username: ")
			password = getpass.getpass("Password: ")
			otp = input("OTP (or press Enter to skip): ") or None
			return await UserCredential.create(api, redirect_uri, username, password, otp=otp, scope=scope)
		except SignInError:
			print("retry...")
