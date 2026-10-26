#!/usr/bin/env python3
"""Call the checker's havoc method 100 times from each of NUM_THREADS threads and print request timings."""
import json
import sys
import threading
import time
import urllib.request

CHECKER_URL = "http://localhost:8000/"
SERVICE_ADDRESS = sys.argv[1] if len(sys.argv) > 1 else "172.20.0.1"  # address the checker uses to reach the service
VARIANT_ID = 1
NUM_THREADS = 8
REQUESTS = 100  # per thread


def havoc(i: int) -> str:
    task = {
        "taskId": i,
        "method": "havoc",
        "address": SERVICE_ADDRESS,
        "teamId": 1,
        "teamName": "hammer",
        "currentRoundId": 1,
        "relatedRoundId": 1,
        "flag": None,
        "variantId": VARIANT_ID,
        "timeout": 30000,
        "roundLength": 60000,
        "taskChainId": f"hammer_havoc_{i}",
    }
    request = urllib.request.Request(CHECKER_URL, data=json.dumps(task).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    if result.get("result") != "OK":
        print(f"request {i}: {result.get('result')} {result.get('message')!r}")
    return result.get("result")


def worker(thread_id: int, times: list[float], failures: list[int]) -> None:
    for i in range(thread_id * REQUESTS, (thread_id + 1) * REQUESTS):
        start = time.monotonic()
        try:
            ok = havoc(i) == "OK"
        except Exception as e:
            print(f"request {i}: {e!r}")
            ok = False
        times.append(time.monotonic() - start)  # list.append is thread-safe
        if not ok:
            failures.append(i)


def main() -> None:
    times: list[float] = []
    failures: list[int] = []
    start = time.monotonic()
    threads = [threading.Thread(target=worker, args=(t, times, failures)) for t in range(NUM_THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    total = time.monotonic() - start
    print(f"{len(times)} requests ({NUM_THREADS} threads x {REQUESTS}), {len(failures)} failed, {total:.1f}s total")
    print(f"max: {max(times):.3f}s")
    print(f"avg: {sum(times) / len(times):.3f}s")


if __name__ == "__main__":
    main()
