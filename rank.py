#!/usr/bin/python3
from typing import TextIO
import asyncio
from API42 import *
from utils import put_waiting, chunks
import json

async def get_level(api:API42, credential:Credential, users:list[int], cursus:int) -> list:
	query = {"sort":"-level", "cursus_id": cursus, "page[size]": 100, "page[number]": 1}
	data = 	[(u["user"]["id"], u["level"]) for s in await asyncio.gather(*[
			api.get(credential, "/v2/cursus_users", {**query, "filter[user_id]": ",".join([str(user) for user in user_list])})
		for user_list in chunks(users, 100)])
		for u in s]
	return sorted(data, key=lambda x: x[1], reverse=True)

async def get_score(api:API42, credential:Credential, users:list[int], cursus:int) -> list:
	query = {"sort":"-this_year_score", "cursus_id": cursus, "page[size]": 100, "page[number]": 1}
	data = [(u["user_id"], u["score"]) for s in await asyncio.gather(*[
			api.get(credential, "/v2/coalitions_users", {**query, "filter[user_id]": ",".join([str(user) for user in user_list])})
		for user_list in chunks(users, 100)])
		for u in s]
	return sorted(data, key=lambda x: x[1], reverse=True)

async def has_cursus(api:API42, credential:Credential, users:list[int], cursus:int) -> list:
	query = {"cursus_id": cursus, "page[size]": 100, "page[number]": 1}
	data = 	[u["user"]["id"] for s in await asyncio.gather(*[
			api.get(credential, "/v2/cursus_users", {**query, "filter[user_id]": ",".join([str(user) for user in user_list])})
		for user_list in chunks(users, 100)])
		for u in s]
	return {user: user in data for user in users}

async def get_project_mark(api:API42, credential:Credential, users:list[int], project:int) -> list:
	query = {"filter[marked]": "true", "filter[project_id]": project, "page[size]": 100, "page[number]": 1}
	data = dict.fromkeys(users)
	data |= {u["user"]["id"]:u["final_mark"] for s in await asyncio.gather(*[
			api.get(credential, "/v2/projects_users", {**query, "filter[user_id]": ",".join([str(user) for user in user_list])})
		for user_list in chunks(users, 100)])
		for u in s}
	return sorted(data.items(), key=lambda x: x[1] if x[1] is not None else -1, reverse=True)

async def main(pisciners:dict[int, str], passed:bool, output:TextIO, client_id:str=None, client_secret=None) -> int:
	api:API42 = make_api_flow(client_id, client_secret)
	credential = await ClientCredential.create(api)
	res = {}
	if passed:
		res["has_cursus"] = has_cursus(api, credential, pisciners.keys(), CURSUS_42_CURSUS)
	res["level_rank"] = get_level(api, credential, pisciners.keys(), CURSUS_C_PISCINE)
	res["score_rank"] = get_score(api, credential, pisciners.keys(), CURSUS_C_PISCINE)
	res["shell_00"] = get_project_mark(api, credential, pisciners.keys(), PROJECTS_C_PISCINE.shell_00)
	res["shell_01"] = get_project_mark(api, credential, pisciners.keys(), PROJECTS_C_PISCINE.shell_01)
	res["c_00"] = get_project_mark(api, credential, pisciners.keys(), PROJECTS_C_PISCINE.c_00)
	res["c_01"] = get_project_mark(api, credential, pisciners.keys(), PROJECTS_C_PISCINE.c_01)
	res["exam_00"] = get_project_mark(api, credential, pisciners.keys(), PROJECTS_C_PISCINE.exam_00)
	for k, v in zip(res.keys(), await put_waiting("Please wait",asyncio.gather(*res.values()))):
		res[k] = v
	is_passed = res.pop("has_cursus", None)
	for k, v in res.items():
		output.write(f"{k}\n")
		for i, (user_id, value) in enumerate(v, 1):
			output.write(f"{i}\t: {pisciners[user_id]} ")
			if passed:
				output.write(("Passed" if is_passed[user_id] else "Failed") + " ")
			output.write(f"{value}\n")
		output.write("\n")
	return 0

if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser()
	parser.add_argument("pisciners", nargs='+', type=argparse.FileType(), help="pisciners json file")
	parser.add_argument("-p", "--passed", action='store_true')
	parser.add_argument("-o", "--output", type=argparse.FileType("w"), default='rank.txt',)
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	pisciners = {int(k):v for tmp in args.pisciners for k, v in json.load(tmp).items()}
	exit(asyncio.run(main(pisciners, args.passed, args.output, args.client_id, args.client_secret)))
