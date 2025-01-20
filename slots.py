#!/usr/bin/python3
import asyncio
import API42
from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
from math import ceil
from utils import put_waiting

# async def get_slots(user:API42.UserCredential) -> list:
# 	query = {"sort": "-begin_at", "filter[future]":"true", "page[size]": 100}
# 	data = []
# 	i = 1
# 	while True:
# 		data += [{
# 				"begin_at": slot["begin_at"],
# 				"end_at": slot["end_at"],
# 				"scale_team": slot["scale_team"]["correcteds"]["login"]if slot["scale_team"] else None
# 			} for slot in
# 		await user.get("/v2/me/slots", {**query, "page[number]": i})]
# 		if len(data) < 100:
# 			break
# 	return data

async def set_slots(user:API42.UserCredential, user_id:int, start:datetime, interval:timedelta) -> str:
	params={"slot[user_id]":user_id, "slot[begin_at]":  start.isoformat(), "slot[end_at]":  (start + interval).isoformat()}
	res = await user._request("POST", f"/v2/slots", params=params)
	if res.status_code != 201:
		data = res.json()
		return str(data)
	else:
		return "Slot created"

async def main(minutes:int, client_id:str=None, client_secret=None) -> int:
	api = await API42.make_api_flow(client_id, client_secret)
	code = await API42.signin_flow(api._client_id, "http://localhost:4242/")
	user:API42.UserCredential = await api.user_credential(code)
	user_id = (await user.me())["id"]
	now = datetime.now(ZoneInfo("Asia/Tokyo"))
	minute = (ceil(now.minute / 15) + 2) * 15
	hour = now.hour + 1 if 60 < minute  else now.hour
	minute = minute % 60
	now = now.replace(second=0, microsecond=0, minute=minute, hour=hour)
	await put_waiting("Setting slots", set_slots(user, user_id, now, timedelta(minutes=minutes)))

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("minutes", type=int, default=45)
	parser.add_argument("--client_id", type=str, default=None)
	parser.add_argument("--client_secret", type=str, default=None)
	args = parser.parse_args()
	exit(asyncio.run(main(args.minutes, args.client_id, args.client_secret)))
