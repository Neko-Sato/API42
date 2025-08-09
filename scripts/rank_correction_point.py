#!/usr/bin/python3
import asyncio
from API42 import API42, Credential, ClientCredential, make_api_flow, CAMPUS_TOKYO, CURSUS_42_CURSUS
from utils import put_waiting

async def get_rank_correction_point(api:API42, credential:Credential, campus: int) -> list[tuple[str, int]]:
	query = {"campus_id": campus, "cursus_id": CURSUS_42_CURSUS, "filter[kind]": "student", "page[size]": 100}
	users = {}
	i = 1
	while True:
		tmp = {u["login"]: u["correction_point"] for u in 
			await put_waiting(f"Got page {i}", api.get(credential, "/v2/users", {**query, "page[number]": i}))}
		users.update(tmp)
		if len(tmp) < 100:
			break
		i += 1
	return [(k, v) for k, v in sorted(users.items(), key=lambda x: x[1], reverse=True)]

async def main(campus:int, client_id:str=None, client_secret=None) -> int:
	api:API42 = make_api_flow(client_id, client_secret)
	credential:ClientCredential = await ClientCredential.create(api)
	data = await get_rank_correction_point(api, credential, campus)
	with open(f"rank_correction_point.txt", "w") as f:
		for user in data:
			f.write(f"{user[0]:20}: {user[1]}\n")
	return 0

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--campus", type=int, default=CAMPUS_TOKYO)
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	exit(asyncio.run(main(args.campus, args.client_id, args.client_secret)))
