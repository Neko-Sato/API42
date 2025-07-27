#!/usr/bin/python3
import asyncio
from ..API42 import API42, Credential, ClientCredential, make_api_flow
import json
from utils import put_waiting
from math import ceil

# Create the first_name, last_name set from user_id and search for accounts with the same name.

async def get_names(api:API42, credential:Credential, users:list[int]) -> set[tuple[str, str]]:
	query = {"filter[id]": ",".join([str(user) for user in users]), "page[size]": 100}
	data = 	{(u["first_name"], u["last_name"]) for s in await asyncio.gather(*[
			api.get(credential, "/v2/users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s}
	return data

async def get_repeater(api:API42, credential:Credential, names:set[tuple[str, str]]):
	for first_name, last_name in names:
		query = {"filter[first_name]": first_name, "filter[last_name]": last_name}
		data = 	await api.get(credential, "/v2/users", query)
		if 1 < len(data):
			yield [u['login'] for u in data]

async def main(pisciners:dict[int, str], client_id:str=None, client_secret=None) -> int:
	api:API42 = make_api_flow(client_id, client_secret)
	credential:Credential = await ClientCredential.create(api)
	names = await put_waiting("Getting names", get_names(api, credential, pisciners.keys()))
	async for repeater in get_repeater(api, credential, names):
		print(repeater)

if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser()
	parser.add_argument("pisciners", nargs='+', type=argparse.FileType(), help="pisciners json file")
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	pisciners = {int(k):v for tmp in args.pisciners for k, v in json.load(tmp).items()}
	exit(asyncio.run(main(pisciners, args.client_id, args.client_secret)))
