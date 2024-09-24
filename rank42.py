#!/usr/bin/python3
import asyncio
import API42
import os
from math import ceil

CAMPUSES_TOKYO = 26
CURSUS_C_PISCINE = 9
CURSUS_42_CURSUS = 21
YEAR = 2024
MONTH = 9

async def get_level(credential:API42.Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"-level", "cursus_id": cursus, "page[size]": 100}
	data = 	[(u["user"]["id"], u["level"]) for s in await asyncio.gather(*[
			credential.get("/v2/cursus_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return data

async def get_score(credential:API42.Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"-this_year_score", "cursus_id": cursus, "page[size]": 100}
	data = [(u["user_id"], u["score"]) for s in await asyncio.gather(*[
			credential.get("/v2/coalitions_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return data

async def has_cursus(credential:API42.Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "cursus_id": cursus, "page[size]": 100}
	data = 	[u["user"]["id"] for s in await asyncio.gather(*[
			credential.get("/v2/cursus_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s]
	return {user: user in data for user in users}

async def get_project_rank(credential:API42.Credential, users:list[int], project:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "filter[marked]": "true", "filter[project_id]": project, "page[size]": 100}
	data = 	{u["user"]["id"]:u["final_mark"] for s in await asyncio.gather(*[
			credential.get("/v2/projects_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s}
	return sorted(data.items(), key=lambda x: x[1], reverse=True)

async def main() -> int:
	client_id = os.getenv("API42_CLIENT_ID")
	client_secret = os.getenv("API42_CLIENT_SECRET")
	if not client_id or not client_secret:
		print("Please set API42_CLIENT_ID and API42_CLIENT_SECRET")
		return 1
	api = API42.API42(client_id, client_secret)
	credential = await api.client_credential()
	pisciners = await credential.get_pisciners(CAMPUSES_TOKYO, YEAR, MONTH)
	is_passed = await has_cursus(credential, pisciners.keys(), CURSUS_42_CURSUS)
	level_rank = await get_level(credential, pisciners.keys(), CURSUS_C_PISCINE)
	print("level_rank")
	for i, (user_id, level) in enumerate(level_rank, 1):
		print(i, pisciners[user_id], "Passed" if is_passed[user_id] else "Failed", level)
	score_rank = await get_score(credential, pisciners.keys(), CURSUS_C_PISCINE)
	print("score_rank")
	for i, (user_id, score) in enumerate(score_rank, 1):
		print(i, pisciners[user_id], "Passed" if is_passed[user_id] else "Failed", score)
	return 0

if __name__ == "__main__":
	exit(asyncio.run(main()))