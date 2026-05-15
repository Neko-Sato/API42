#!/usr/bin/env python3
from typing import TextIO
import asyncio
from api42 import API42Client, CAMPUS_TOKYO, CURSUS_42_CURSUS
from tqdm.asyncio import tqdm_asyncio
import os


async def get_rank_correction_point(client: API42Client, campus: int | None = None) -> list[tuple[str, int]]:
    query = {"cursus_id": CURSUS_42_CURSUS,
             "filter[kind]": "student", "page[size]": 100}
    if campus is not None:
        query["campus_id"] = campus
    result = {}
    with tqdm_asyncio(desc=f"Fetching correction_point") as pbar:
        tmp = await client.get(
            "/v2/users",
            params={**query, "page[number]": 1},
        )
        tmp.raise_for_status()
        users = {u["login"]: u["correction_point"] for u in tmp.json()}
        result.update(users)
        total_users = int(tmp.headers["x-total"])
        per_page = int(tmp.headers["x-per-page"])
        last_page = (total_users + per_page - 1) // per_page
        pbar.total = last_page
        pbar.update(1)
        if last_page > 1:
            tasks = [
                client.get("/v2/users", params={**query, "page[number]": page})
                for page in range(2, last_page + 1)
            ]
            for future in asyncio.as_completed(tasks):
                res = await future
                res.raise_for_status()
                page_users = {u["login"]: u["correction_point"]
                              for u in res.json()}
                result.update(page_users)
                pbar.update(1)
    return [(k, v) for k, v in sorted(result.items(), key=lambda x: x[1], reverse=True)]


async def main(campus: int | None, output: TextIO, client_id: str = None, client_secret=None) -> int:
    if client_id is None and client_secret is None:
        client_id = client_id or os.getenv("API42_CLIENT_ID")
        client_secret = client_secret or os.getenv("API42_CLIENT_SECRET")
    if client_id is None or client_secret is None:
        print("client_id and client_secret are required")
        return 1

    client: API42Client = API42Client(client_id, client_secret, None)
    await client.fetch_token()
    data = await get_rank_correction_point(client, campus)
    output.truncate(0)
    output.seek(0)
    for user in data:
        output.write(f"{user[0]:20}: {user[1]}\n")
    return 0

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--campus", type=int, default=CAMPUS_TOKYO)
    parser.add_argument(
        "-o", "--output", type=argparse.FileType("w"), default='rank_correction_point.txt')
    parser.add_argument("--client_id", type=str, default=None)
    parser.add_argument("--client_secret", type=str, default=None)
    args = parser.parse_args()
    exit(asyncio.run(main(args.campus, args.output, args.client_id, args.client_secret)))
