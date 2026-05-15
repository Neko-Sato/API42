#!/usr/bin/env python3
import asyncio
from api42 import API42Client
import json
from math import ceil
import os
from tqdm.asyncio import tqdm_asyncio

# Create the first_name, last_name set from user_id and search for accounts with the same name.


async def get_names(client: API42Client, users: list[int]) -> set[tuple[str, str]]:
    query = {"filter[id]": ",".join([str(user)
                                    for user in users]), "page[size]": 100}
    total_pages = ceil(len(users) / 100)

    async def fetch(page):
        res = await client.get("/v2/users", params={**query, "page[number]": page})
        return {(u["first_name"], u["last_name"]) for u in res.json()}

    results = await tqdm_asyncio.gather(
        *[fetch(i) for i in range(1, total_pages + 1)],
        desc="Getting names",
    )
    data = {x for res in results for x in res}
    return data


async def get_repeater(client: API42Client, names: set[tuple[str, str]]) -> dict[tuple[str, str], list[str]]:
    async def fetch(first_name, last_name):
        res = await client.get("/v2/users", params={"filter[first_name]": first_name, "filter[last_name]": last_name})
        logins = [u["login"] for u in res.json()]
        if len(logins) > 1:
            tqdm_asyncio.write(f"{first_name} {last_name}: {logins}")
        return {(first_name, last_name): logins}
    results = await tqdm_asyncio.gather(
        *[fetch(first_name, last_name) for first_name, last_name in names],
        desc="Searching repeaters",
    )
    data = {k: v for res in results for k, v in res.items() if len(v) > 1}
    return data


async def main(pisciners: dict[int, str], client_id: str = None, client_secret=None) -> int:
    if client_id is None and client_secret is None:
        client_id = client_id or os.getenv("API42_CLIENT_ID")
        client_secret = client_secret or os.getenv("API42_CLIENT_SECRET")
    if client_id is None or client_secret is None:
        print("client_id and client_secret are required")
        return 1

    client = await API42Client.create(client_id, client_secret)
    names = await get_names(client, list(pisciners.keys()))
    await get_repeater(client, names)
    return 0

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("pisciners", nargs='+',
                        type=argparse.FileType(), help="pisciners json file")
    parser.add_argument("--client_id", type=str, default=None)
    parser.add_argument("--client_secret", type=str, default=None)
    args = parser.parse_args()
    pisciners = {int(k): v for tmp in args.pisciners for k,
                 v in json.load(tmp).items()}
    exit(asyncio.run(main(pisciners, args.client_id, args.client_secret)))
