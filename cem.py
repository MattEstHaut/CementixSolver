#!/usr/bin/env python3

import json
import asyncio
import aiohttp
import time
import random

url = "https://cemantix.certitudes.org/score"
wordlist = open("wordlist.txt").read().split("\n")
headers = json.loads(open("headers.json").read())

random.shuffle(wordlist)
batch_size = 1000


def next_batch(wordlist, batch_size):
    for i in range(0, len(wordlist), batch_size):
        yield wordlist[i:i+batch_size]


async def get_score(session, word):
    async with session.post(url, headers=headers, data={"word": word}) as response:
        result = await response.json()
        return word, result["score"] if "score" in result.keys() else None


async def get_scores(session, batch):
    tasks = [get_score(session, word) for word in batch]
    return await asyncio.gather(*tasks)


def get_best(scores):
    return max(scores, key=lambda x: 0 if x[1] is None else x[1])


async def next_step(session, batch):
    t0 = time.time()
    scores = await get_scores(session, batch)
    best, score = get_best(scores)
    t = round(time.time() - t0, 1)
    return best, score, t


async def main():
    t0 = time.time()
    best, score = None, None
    tested = 0

    async with aiohttp.ClientSession() as session:
        for step, batch in enumerate(next_batch(wordlist, batch_size)):
            batch_best, batch_score, t = await next_step(session, batch)
            best, score = get_best([(batch_best, batch_score), (best, score)])
            tested += len(batch)
            if score == 1.: break
            
            message = "Batch {} tested in {}s ({:.1f}w/s) => best {} ({})"
            print(message.format(step, t, len(batch)/t, best, score))

    dt = time.time() - t0
    print("{} words tested in {:.1f}s ({:.1f}w/s)".format(tested, dt, tested/dt))
    print(f"Best word found: {best} ({score})")

if __name__ == "__main__":
    asyncio.run(main())
