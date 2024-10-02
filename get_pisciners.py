#!/usr/bin/python3
import asyncio
from API42 import API42, Credential, make_api_flow, CAMPUS_TOKYO
from utils import put_waiting
import calendar
import json

async def get_pisciners(api:API42, campus: int, year: int, month: int) -> dict[int, str]:
	query = {"campus_id": campus, "filter[pool_month]": calendar.month_name[month].lower(), "filter[pool_year]": year, "page[size]": 100}
	users = {}
	i = 1
	while True:
		tmp = {u["id"]: u["login"] for u in await api.get("/v2/users", {**query, "page[number]": i})}
		users.update(tmp)
		if len(tmp) < 100:
			break
		i += 1
	return users

async def main(campus:int, year:int, month:int, client_id:str=None, client_secret=None) -> int:
	api:API42 = await make_api_flow(client_id, client_secret)
	credential:Credential = await api.client_credential()
	data = await put_waiting("Getting pisciners", get_pisciners(credential, campus, year, month))
	with open(f"pisciners_{year}_{month}.json", "w") as f:
		json.dump(data, f, indent=4)
	return 0

if __name__ == "__main__":
	import argparse
	from datetime import datetime

	parser = argparse.ArgumentParser()
	now = datetime.now()
	parser.add_argument("-c", "--campus", type=int, default=CAMPUS_TOKYO)
	parser.add_argument("-y", "--year", type=int, default=now.year)
	parser.add_argument("-m", "--month", type=int, default=now.month)
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	exit(asyncio.run(main(args.campus, args.year, args.month, args.client_id, args.client_secret)))
