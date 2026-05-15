#!/usr/bin/env python3
from typing import TextIO
import asyncio
from api42 import API42Client, CURSUS_C_PISCINE, CURSUS_42_CURSUS, PROJECTS_C_PISCINE
from tqdm.asyncio import tqdm_asyncio
import json
import os


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


async def get_level(client: API42Client, users: list[int], cursus: int, **kwds) -> list:
    query = {
        "sort": "-level",
        "cursus_id": cursus,
        "page[size]": 100,
        "page[number]": 1,
    }

    async def fetch(chunk):
        res = await client.get(
            "/v2/cursus_users",
            params={
                **query, "filter[user_id]": ",".join(str(u) for u in chunk)},
        )
        return [(u["user"]["id"], u["level"]) for u in res.json()]

    results = await tqdm_asyncio.gather(
        *[fetch(chunk) for chunk in chunks(users, 100)],
        desc="Fetching levels",
        **kwds,
    )
    data = [x for res in results for x in res]
    return sorted(data, key=lambda x: x[1], reverse=True)


async def get_score(client: API42Client, users: list[int], cursus: int, **kwds) -> list:
    query = {
        "sort": "-this_year_score",
        "cursus_id": cursus,
        "page[size]": 100,
        "page[number]": 1,
    }

    async def fetch(chunk):
        res = await client.get(
            "/v2/coalitions_users",
            params={
                **query, "filter[user_id]": ",".join(str(u) for u in chunk)},
        )
        return [(u["user_id"], u["score"]) for u in res.json()]

    results = await tqdm_asyncio.gather(
        *[fetch(chunk) for chunk in chunks(users, 100)],
        desc="Fetching scores",
        **kwds,
    )
    data = [x for res in results for x in res]
    return sorted(data, key=lambda x: x[1], reverse=True)


async def has_cursus(
    client: API42Client, users: list[int], cursus: int, **kwds
) -> dict[int, bool]:
    query = {"cursus_id": cursus, "page[size]": 100, "page[number]": 1}

    async def fetch(chunk):
        res = await client.get(
            "/v2/cursus_users",
            params={
                **query, "filter[user_id]": ",".join(str(u) for u in chunk)},
        )
        return {u["user"]["id"] for u in res.json()}

    results = await tqdm_asyncio.gather(
        *[fetch(chunk) for chunk in chunks(users, 100)],
        desc="Fetching cursus membership",
        **kwds,
    )
    found = {x for res in results for x in res}
    return {user: user in found for user in users}


async def get_project_mark(
    client: API42Client, users: list[int], project: int, **kwds
) -> list:
    query = {
        "filter[marked]": "true",
        "filter[project_id]": project,
        "page[size]": 100,
        "page[number]": 1,
    }

    async def fetch(chunk):
        res = await client.get(
            "/v2/projects_users",
            params={
                **query, "filter[user_id]": ",".join(str(u) for u in chunk)},
        )
        return {u["user"]["id"]: u["final_mark"] for u in res.json()}

    results = await tqdm_asyncio.gather(
        *[fetch(chunk) for chunk in chunks(users, 100)],
        desc=f"Fetching project {project}",
        **kwds,
    )
    data = dict.fromkeys(users)
    data |= {k: v for res in results for k, v in res.items()}
    return sorted(
        data.items(), key=lambda x: x[1] if x[1] is not None else -1, reverse=True
    )


async def main(
    pisciners: dict[int, str],
    passed: bool,
    output: TextIO,
    client_id: str = None,
    client_secret=None,
) -> int:
    if client_id is None and client_secret is None:
        client_id = client_id or os.getenv("API42_CLIENT_ID")
        client_secret = client_secret or os.getenv("API42_CLIENT_SECRET")
    if client_id is None or client_secret is None:
        print("client_id and client_secret are required")
        return 1

    client: API42Client = API42Client(client_id, client_secret, None)
    await client.fetch_token()
    user_ids = list(pisciners.keys())

    tasks = {}
    if passed:
        tasks["has_cursus"] = has_cursus(client, user_ids, CURSUS_42_CURSUS)
    tasks["level_rank"] = get_level(client, user_ids, CURSUS_C_PISCINE)
    tasks["score_rank"] = get_score(client, user_ids, CURSUS_C_PISCINE)

    # tasks["shell_00"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.shell_00)
    # tasks["shell_01"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.shell_01)
    # tasks["c_00"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_00)
    # tasks["c_01"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_01)
    # tasks["exam_00"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.exam_00)
    # tasks["rush_00"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.rush_00)

    # tasks["c_02"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_02)
    # tasks["c_03"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_03)
    # tasks["c_04"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_04)
    # tasks["c_05"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_05)
    # tasks["exam_01"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.exam_01)
    # tasks["rush_01"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.rush_01)

    # tasks["c_06"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_06)
    # tasks["c_07"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_07)
    # tasks["c_08"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_08)
    # tasks["c_09"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_09)
    # tasks["exam_02"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.exam_02)
    # tasks["rush_02"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.rush_02)

    # tasks["bsq"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.bsq)
    # tasks["c_10"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_10)
    # tasks["c_11"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_11)
    # tasks["c_12"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_12)
    # tasks["c_13"] = get_project_mark(client, user_ids, PROJECTS_C_PISCINE.c_13)
    # tasks["final_exam"] = get_project_mark(
    #     client, user_ids, PROJECTS_C_PISCINE.final_exam)

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values())))

    is_passed = results.pop("has_cursus", None)
    for k, v in results.items():
        output.write(f"{k}\n")
        for i, (user_id, value) in enumerate(v, 1):
            output.write(f"{i}\t: {pisciners[user_id]} ")
            if passed:
                output.write(
                    ("Passed" if is_passed[user_id] else "Failed") + " ")
            output.write(f"{value}\n")
        output.write("\n")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pisciners", nargs="+", type=argparse.FileType(), help="pisciners json file"
    )
    parser.add_argument("-p", "--passed", action="store_true")
    parser.add_argument(
        "-o", "--output", type=argparse.FileType("w"), default="rank.txt"
    )
    parser.add_argument("--client_id", type=str, default=None)
    parser.add_argument("--client_secret", type=str, default=None)
    args = parser.parse_args()
    pisciners = {int(k): v for tmp in args.pisciners for k,
                 v in json.load(tmp).items()}
    exit(
        asyncio.run(
            main(
                pisciners, args.passed, args.output, args.client_id, args.client_secret
            )
        )
    )
