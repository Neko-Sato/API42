#!/usr/bin/python3
import asyncio
import API42
from math import ceil
import sys

CAMPUS_TOKYO = 26
CURSUS_C_PISCINE = 9
CURSUS_42_CURSUS = 21
class PROJECTS_C_PISCINE:
	shell_00 = 1255
	shell_01 = 1256
	c_12 = 1268
	c_13 = 1271
	c_11 = 1267
	c_10 = 1266
	c_09 = 1265
	c_07 = 1270
	c_08 = 1264
	c_06 = 1263
	c_05 = 1262
	c_04 = 1261
	c_03 = 1260
	c_02 = 1259
	c_01 = 1258
	c_00 = 1257
	bsq = 1305
	rush_02 = 1309
	rush_01 = 1310
	rush_00 = 1308
	final_exam = 1304
	exam_02 = 1303
	exam_01 = 1302
	exam_00 = 1301

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

async def get_project_mark(credential:API42.Credential, users:list[int], project:int) -> list:
	query = {"filter[user_id]": ",".join([str(user) for user in users]), "filter[marked]": "true", "filter[project_id]": project, "page[size]": 100}
	data = 	{u["user"]["id"]:u["final_mark"] for s in await asyncio.gather(*[
			credential.get("/v2/projects_users", {**query, "page[number]": i})
		for i in range(1, ceil(len(users) / 100) + 1)])
		for u in s}
	return sorted(data.items(), key=lambda x: x[1], reverse=True)

async def put_waiting(message:str, waitable):
	if asyncio.isfuture(waitable):
		task = waitable
	else:
		task = asyncio.create_task(waitable)
	try:
		while not task.done():
			for symbol in ['|', '/', '-', '\\']:
				sys.stdout.write(f'\r{message} {symbol}')
				sys.stdout.flush()
				await asyncio.sleep(0.1)
		sys.stdout.write(f'\r{message} OK\n')
		sys.stdout.flush()
	except asyncio.CancelledError:
		task.cancel()
	return await task
	
async def main() -> int:
	api = await API42.make_api_flow()
	credential = await api.client_credential()
	pisciners = {k:v for s in await put_waiting("Getting pisciners", asyncio.gather(
		credential.get_pisciners(CAMPUS_TOKYO, YEAR, 8),
		credential.get_pisciners(CAMPUS_TOKYO, YEAR, 9),
	)) for k, v in s.items()}
	is_passed, level_rank, score_rank, exam_rank = await put_waiting("Please wait", asyncio.gather(
		has_cursus(credential, pisciners.keys(), CURSUS_42_CURSUS),
		get_level(credential, pisciners.keys(), CURSUS_C_PISCINE),
		get_score(credential, pisciners.keys(), CURSUS_C_PISCINE),
		get_project_mark(credential, pisciners.keys(), PROJECTS_C_PISCINE.final_exam),
	))
	print("level_rank")
	for i, (user_id, level) in enumerate(level_rank, 1):
		print(i, pisciners[user_id], "Passed" if is_passed[user_id] else "Failed", level)
	print("score_rank")
	for i, (user_id, score) in enumerate(score_rank, 1):
		print(i, pisciners[user_id], "Passed" if is_passed[user_id] else "Failed", score)
	print("exam_rank")
	for i, (user_id, mark) in enumerate(exam_rank, 1):
		print(i, pisciners[user_id], "Passed" if is_passed[user_id] else "Failed", mark)
	return 0

if __name__ == "__main__":
	exit(asyncio.run(main()))
