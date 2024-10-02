#!/usr/bin/python3
import asyncio
from API42 import API42, Credential, make_api_flow, CURSUS_C_PISCINE
from utils import put_waiting
from math import ceil

#
# Output active PISCINER in decreasing rank order.
# These people should definitely lifeserve.
#

async def get_level(credential:Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"level", "cursus_id": cursus, "page[size]": 100}
	data = 	[(u["user"]["id"], u["level"]) for s in await asyncio.gather(*[
			credential.get("/v2/cursus_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return data

async def get_location(credential:Credential, users:list[int]) -> dict:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "filter[active]":"true", "page[size]": 100}
	data = 	{u["user"]["id"]: u["host"] for s in await asyncio.gather(*[
			credential.get("/v2/locations", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s}
	return data

async def main(pisciners:dict[int, str], cursus:int, client_id:str=None, client_secret=None) -> int:
	api:API42 = await make_api_flow(client_id, client_secret)
	credential = await api.client_credential()
	level_rank, locations = await put_waiting("Please wait", asyncio.gather(
		get_level(credential, pisciners.keys(), cursus),
		get_location(credential, pisciners.keys()),
	))
	for user_id, level in level_rank:
		location = locations.get(user_id)
		if location:
			print(int(level), pisciners[user_id], location)
	return 0

if __name__ == "__main__":
	import argparse
	import json

	parser = argparse.ArgumentParser()
	parser.add_argument("pisciners", type=argparse.FileType(), help="pisciners json file")
	parser.add_argument("--cursus", type=int, default=CURSUS_C_PISCINE)
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	pisciners = {int(k):v for k, v in json.load(args.pisciners).items()}
	exit(asyncio.run(main(pisciners, args.cursus, args.client_id, args.client_secret)))
