import asyncio
import API42
import os
import calendar

CAMPUSES = 26
CURSUS = 9
YEAR = 2024
MONTH = 9

async def get_pisciners(credential:API42.Credential, campus:int, year:int, month:int) -> dict:
	query = {"campus_id": campus, "filter[pool_month]": calendar.month_name[month].lower(), "filter[pool_year]": year, "page[size]": 100}
	users = {u["id"]:u["login"] for s in await asyncio.gather(*[
			credential.get("/v2/users", {**query, "page[number]": i})
		for i in range(1, 3)])
		for u in s}
	return users

async def get_level(credential:API42.Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"-level", "cursus_id": cursus, "page[size]": 100}
	data = 	[(u["user"]["id"], u["level"]) for s in await asyncio.gather(*[
			credential.get("/v2/cursus_users", {**query, "page[number]": i})
		for i in range(1, 3)])
		for u in s]
	return data

async def get_score(credential:API42.Credential, users:list[int], cursus:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "sort":"-this_year_score", "cursus_id": cursus, "page[size]": 100}
	data = [(u["user_id"], u["score"]) for s in await asyncio.gather(*[
			credential.get("/v2/coalitions_users", {**query, "page[number]": i})
		for i in range(1, 3)])
		for u in s]
	return data

async def main() -> int:
	client_id = os.getenv("API42_CLIENT_ID")
	client_secret = os.getenv("API42_CLIENT_SECRET")
	if not client_id or not client_secret:
		print("Please set API42_CLIENT_ID and API42_CLIENT_SECRET")
		return 1
	api = API42.API42(client_id, client_secret)
	credential = await api.client_credential()
	pisciners = await get_pisciners(credential, CAMPUSES, YEAR, MONTH)
	print("level_rank")
	for i, user in enumerate(await get_level(credential, list(pisciners.keys()), CURSUS), 1):
		print(i, pisciners[user[0]], user[1])	
	print("score_rank")
	for i, user in enumerate(await get_score(credential, list(pisciners.keys()), CURSUS), 1):
		print(i, pisciners[user[0]], user[1])
	return 0

if __name__ == "__main__":
	exit(asyncio.run(main()))