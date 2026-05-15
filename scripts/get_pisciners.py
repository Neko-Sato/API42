#!/usr/bin/env python3
import asyncio
from api42 import API42Client, CAMPUS_TOKYO
from tqdm.asyncio import tqdm_asyncio
import calendar
import json
import os
from pathlib import Path


async def get_pisciners(client: API42Client, campus: int, year: int, month: int) -> dict[int, str]:
    query = {
        "campus_id": campus,
        "filter[pool_month]": calendar.month_name[month].lower(),
        "filter[pool_year]": year,
        "page[size]": 100,
    }
    result = {}
    with tqdm_asyncio(desc=f"Fetching pisciners {year}-{month:02}") as pbar:
        first_res = await client.get(
            "/v2/users",
            params={**query, "page[number]": 1},
        )
        first_res.raise_for_status()
        users = {u["id"]: u["login"] for u in first_res.json()}
        result.update(users)
        total_users = int(first_res.headers["x-total"])
        per_page = int(first_res.headers["x-per-page"])
        last_page = (total_users + per_page - 1) // per_page
        pbar.total = last_page
        pbar.update(1)
        if last_page <= 1:
            return result
        tasks = [
            client.get("/v2/users", params={**query, "page[number]": page})
            for page in range(2, last_page + 1)
        ]
        for future in asyncio.as_completed(tasks):
            res = await future
            res.raise_for_status()
            page_data = {u["id"]: u["login"] for u in res.json()}
            result.update(page_data)
            pbar.update(1)
    return result


async def main(campus: int, pools: list[tuple[int, int]], client_id: str = None, client_secret=None) -> int:
    if client_id is None and client_secret is None:
        client_id = client_id or os.getenv("API42_CLIENT_ID")
        client_secret = client_secret or os.getenv("API42_CLIENT_SECRET")
    if client_id is None or client_secret is None:
        print("client_id and client_secret are required")
        return 1
    client: API42Client = await API42Client.create(client_id, client_secret)
    directory = Path("./pisciners")
    directory.mkdir(exist_ok=True)
    tmp = await asyncio.gather(*[get_pisciners(client, campus, year, month) for year, month in pools])
    for (year, month), data in zip(pools, tmp):
        with open(directory.joinpath(f"{year}_{month}.json"), "w") as f:
            json.dump(data, f, indent=4)
    return 0


def parse_pool(value: str) -> tuple[int, int]:
    if len(value) != 7 or value[4] != "-":
        raise argparse.ArgumentTypeError(
            "expected format: yyyy-mm"
        )
    try:
        year = int(value[:4])
        month = int(value[5:])
    except ValueError:
        raise argparse.ArgumentTypeError(
            "expected format: yyyy-mm"
        )
    if not 1 <= month <= 12:
        raise argparse.ArgumentTypeError(
            "month must be between 1 and 12"
        )
    return year, month


if __name__ == "__main__":
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser()
    now = datetime.now()
    parser.add_argument("-c", "--campus", type=int, default=CAMPUS_TOKYO)
    parser.add_argument("pools", nargs="+", type=parse_pool,
                        default=[(now.year, now.month)])
    parser.add_argument("--client_id", type=str, default=None)
    parser.add_argument("--client_secret", type=str, default=None)
    args = parser.parse_args()
    exit(asyncio.run(main(args.campus, args.pools, args.client_id, args.client_secret)))
