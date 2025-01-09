#!/usr/bin/python3
import asyncio
from API42 import API42, Credential, make_api_flow
import json
from utils import put_waiting
from math import ceil

# Create the first_name, last_name set from user_id and search for accounts with the same name.

async def get_names(credential:Credential, users:list[int]) -> set[tuple[str, str]]:
	query = {"filter[id]": ",".join([str(user) for user in users]), "page[size]": 100}
	data = 	{(u["first_name"], u["last_name"]) for s in await asyncio.gather(*[
			credential.get("/v2/users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s}
	return data

async def get_repeater(credential:Credential, names:set[tuple[str, str]]):
	for first_name, last_name in names:
		query = {"filter[first_name]": first_name, "filter[last_name]": last_name}
		data = 	await credential.get("/v2/users", query)
		if 1 < len(data):
			yield [u['login'] for u in data]

async def main(pisciners:dict[int, str], client_id:str=None, client_secret=None) -> int:
	api:API42 = await make_api_flow(client_id, client_secret)
	credential:Credential = await api.client_credential()
	names = await put_waiting("Getting names", get_names(credential, pisciners.keys()))
	async for repeater in get_repeater(credential, names):
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
