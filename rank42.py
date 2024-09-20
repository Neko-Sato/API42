import asyncio
import API42
import os

async def get_level_rank(credential:API42.Credential) -> list:
	query = {"cursus_id": 9, "filter[campus_id]": 26, "sort": "-level", "range[created_at]":"2024-08-20,now", "page[size]": 100}
	users = [u for s in await asyncio.gather(
		credential.get("/v2/cursus_users", {**query, "page[number]": 1}),
		credential.get("/v2/cursus_users", {**query, "page[number]": 2})
		) for u in s]
	return [{"rank": i, "user_id": user["user"]["id"] , "login": user["user"]["login"], "level": user["level"]}
		 for i, user in enumerate(users, 1)]

async def get_score_rank(credential:API42.Credential) -> dict:
	query = {"filter[coalition_id]": "61,62,63", "sort": "-this_year_score", "range[created_at]":"2024-08-20,now", "page[size]": 100}
	users = [u for s in await asyncio.gather(
		credential.get("/v2/coalitions_users", {**query, "page[number]": 1}),
		credential.get("/v2/coalitions_users", {**query, "page[number]": 2})
		) for u in s]
	query = {"filter[id]": ",".join([str(user["user_id"]) for user in users]), "page[size]": 100}
	login = {i["id"]:i["login"] for s in await asyncio.gather(
		credential.get("/v2/users", {**query, "page[number]": 1}),
		credential.get("/v2/users", {**query, "page[number]": 2})
		) for i in s}
	return [{"rank": i, "login": login.get(user["user_id"], "Unknown"), "score": user["score"]}
		 for i, user in enumerate(users, 1)]

async def get_rank(credential:API42.Credential) -> tuple[list, list]:
	# return await asyncio.gather(get_level_rank(credential), get_score_rank(credential))
	# 効率的に取得しようと非同期にしたものの429エラーになりやがるからここは同期で取得する
	return await get_level_rank(credential), await get_score_rank(credential)

async def main():
	client_id = os.getenv("API42_CLIENT_ID")
	client_secret = os.getenv("API42_CLIENT_SECRET")
	if not client_id or not client_secret:
		print("Please set API42_CLIENT_ID and API42_CLIENT_SECRET")
		return 1
	api = API42.API42(client_id, client_secret)
	credential = await api.client_credential()
	level_rank, score_rank = await get_rank(credential)
	print("level_rank")
	for user in level_rank:
		print(user["rank"], user["login"], user["level"])
	print("score_rank")
	for user in score_rank:
		print(user["rank"], user["login"], user["score"])

asyncio.run(main())