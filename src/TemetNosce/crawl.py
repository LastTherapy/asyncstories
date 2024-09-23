import aiohttp
import asyncio
import argparse
from typing import List


async def send_link(urls: List[str]):
    post_url = "http://127.0.0.1:8888/api/v1/tasks"

    async with aiohttp.ClientSession() as session:
        async with session.post(url=post_url, json=urls) as response:
            response_data = await response.json()
            # print(f"Response status: {response.status}")
            # print(f"Response data: {response_data}")
    return response_data.get("id")


# async def check_status(id)

async def check_status(id):
    get_url = f"http://127.0.0.1:8888/api/v1/tasks/{id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=get_url) as response:
            response_data = await response.json()
            # print(f"Response status: {response.status}")
            # print(f"Response data: {response_data}")
    staus = response_data.get("status")
    return staus


async def get_result(id):
    get_url = f"http://127.0.0.1:8888/api/v1/tasks/{id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=get_url) as response:
            response_data = await response.json()
            # print(f"Response status: {response.status}")
            # print(f"Response data: {response_data}")
    return response_data


async def main(urls: List[str]):
    id = await send_link(urls)
    while True:
        status = await check_status(id)
        if status == "ready":
            print(status)
            break
        else:
            print(status)
        await asyncio.sleep(1)
    data = await get_result(id)
    for k, v in data.get("result").items():
        print(f"{k}\t{v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'urls', nargs='+', help='url or many urls to crawl'
    )
    args = parser.parse_args()
    asyncio.run(main(args.urls))
