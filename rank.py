#!/usr/bin/python3
import asyncio
from API42 import API42, Credential, make_api_flow, CURSUS_C_PISCINE, CURSUS_42_CURSUS
from utils import put_waiting
from math import ceil
import json

async def get_level(credential:Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"-level", "cursus_id": cursus, "page[size]": 100}
	data = 	[(u["user"]["id"], u["level"]) for s in await asyncio.gather(*[
			credential.get("/v2/cursus_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return data

async def get_score(credential:Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"-this_year_score", "cursus_id": cursus, "page[size]": 100}
	data = [(u["user_id"], u["score"]) for s in await asyncio.gather(*[
			credential.get("/v2/coalitions_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return data

async def has_cursus(credential:Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "cursus_id": cursus, "page[size]": 100}
	data = 	[u["user"]["id"] for s in await asyncio.gather(*[
			credential.get("/v2/cursus_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return {user: user in data for user in users}

async def get_project_mark(credential:Credential, users:list[int], project:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "filter[marked]": "true", "filter[project_id]": project, "page[size]": 100}
	data = 	{u["user"]["id"]:u["final_mark"] for s in await asyncio.gather(*[
			credential.get("/v2/projects_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s}
	return sorted(data.items(), key=lambda x: x[1], reverse=True)

async def main(pisciners:dict[int, str], passed:bool, client_id:str=None, client_secret=None) -> int:
	api:API42 = await make_api_flow(client_id, client_secret)
	credential = await api.client_credential()
	is_passed, level_rank, score_rank = await put_waiting("Please wait", asyncio.gather(
		has_cursus(credential, pisciners.keys(), CURSUS_42_CURSUS),
		get_level(credential, pisciners.keys(), CURSUS_C_PISCINE),
		get_score(credential, pisciners.keys(), CURSUS_C_PISCINE),
	))
	with open("rank.txt", "w") as f:
		f.write("level_rank\n")
		for i, (user_id, level) in enumerate(level_rank, 1):
			f.write(f"{i}\t: {pisciners[user_id]} ")
			if passed:
				f.write(("Passed" if is_passed[user_id] else "Failed") + " ")
			f.write(f"{level}\n")
		f.write("\n")
		f.write("score_rank\n")
		for i, (user_id, score) in enumerate(score_rank, 1):
			f.write(f"{i}\t: {pisciners[user_id]} ")
			if passed:
				f.write("Passed" if is_passed[user_id] else "Failed" + " ")
			f.write(f"{score}\n")
	return 0

if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser()
	parser.add_argument("pisciners", nargs='+', type=argparse.FileType(), help="pisciners json file")
	parser.add_argument("-p", "--passed", action='store_true')
	# parser.add_argument("-level" , action='store_true')
	# parser.add_argument("-score" , action='store_true')
	# parser.add_argument("-shell00" , action='store_true')
	# parser.add_argument("-shell01" , action='store_true')
	# parser.add_argument("-c00" , action='store_true')
	# parser.add_argument("-c01" , action='store_true')
	# parser.add_argument("-c02" , action='store_true')
	# parser.add_argument("-c03" , action='store_true')
	# parser.add_argument("-c04" , action='store_true')
	# parser.add_argument("-c05" , action='store_true')
	# parser.add_argument("-c06" , action='store_true')
	# parser.add_argument("-c07" , action='store_true')
	# parser.add_argument("-c08" , action='store_true')
	# parser.add_argument("-c09" , action='store_true')
	# parser.add_argument("-c10" , action='store_true')
	# parser.add_argument("-c11" , action='store_true')
	# parser.add_argument("-c12" , action='store_true')
	# parser.add_argument("-c13" , action='store_true')
	# parser.add_argument("-rush00" , action='store_true')
	# parser.add_argument("-rush01" , action='store_true')
	# parser.add_argument("-rush02" , action='store_true')
	# parser.add_argument("-rush03" , action='store_true')
	# parser.add_argument("-bsq" , action='store_true')
	# parser.add_argument("-exam00" , action='store_true')
	# parser.add_argument("-exam01" , action='store_true')
	# parser.add_argument("-exam02" , action='store_true')
	# parser.add_argument("-finalexam" , action='store_true')
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	pisciners = {int(k):v for tmp in args.pisciners for k, v in json.load(tmp).items()}
	exit(asyncio.run(main(pisciners, args.passed, args.client_id, args.client_secret)))
