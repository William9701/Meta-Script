"""
load_test.py
Simulates 20 concurrent users hitting POST /account/details at the same time.
Run with:
    python load_test.py
"""

import threading
import time
import json
import urllib.request
import urllib.error

# ------------------------------------------------------------------ #
#  Config
# ------------------------------------------------------------------ #

ENDPOINT = "http://localhost:8000/account/details"
NUM_THREADS = 20

PAYLOAD = json.dumps({
    "login": 108050313,
    "password": "-8BdFyEy",
    "server": "MetaQuotes-Demo"
}).encode("utf-8")

# ------------------------------------------------------------------ #
#  Per-thread worker
# ------------------------------------------------------------------ #

results = [None] * NUM_THREADS
errors  = [None] * NUM_THREADS


def worker(index: int):
    start = time.perf_counter()
    try:
        req = urllib.request.Request(
            ENDPOINT,
            data=PAYLOAD,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
            elapsed = time.perf_counter() - start
            results[index] = {
                "thread": index + 1,
                "status": resp.status,
                "elapsed_s": round(elapsed, 3),
                "balance": body.get("account_info", {}).get("balance"),
                "equity": body.get("account_info", {}).get("equity"),
                "open_positions": len(body.get("open_positions", [])),
                "deals_history": len(body.get("deals_history", [])),
            }
    except urllib.error.HTTPError as exc:
        elapsed = time.perf_counter() - start
        errors[index] = {
            "thread": index + 1,
            "status": exc.code,
            "elapsed_s": round(elapsed, 3),
            "error": exc.read().decode(),
        }
    except Exception as exc:
        elapsed = time.perf_counter() - start
        errors[index] = {
            "thread": index + 1,
            "status": None,
            "elapsed_s": round(elapsed, 3),
            "error": str(exc),
        }


# ------------------------------------------------------------------ #
#  Launch all threads simultaneously
# ------------------------------------------------------------------ #

def main():
    print(f"Firing {NUM_THREADS} concurrent requests to {ENDPOINT} ...\n")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(NUM_THREADS)]

    wall_start = time.perf_counter()

    # Start all threads as close together as possible
    for t in threads:
        t.start()

    # Wait for all to finish
    for t in threads:
        t.join()

    wall_elapsed = time.perf_counter() - wall_start

    # ---------------------------------------------------------------- #
    #  Report
    # ---------------------------------------------------------------- #

    successes = [r for r in results if r is not None]
    failures  = [e for e in errors  if e is not None]

    print("=" * 60)
    print(f"  RESULTS  —  {NUM_THREADS} threads, wall time: {wall_elapsed:.3f}s")
    print("=" * 60)

    if successes:
        print(f"\n✓ Successful ({len(successes)}/{NUM_THREADS}):\n")
        print(f"  {'Thread':<8} {'Status':<8} {'Time(s)':<10} {'Balance':<14} {'Equity':<14} {'Positions':<10} {'Deals'}")
        print(f"  {'-'*7:<8} {'-'*6:<8} {'-'*7:<10} {'-'*10:<14} {'-'*10:<14} {'-'*9:<10} {'-'*5}")
        for r in sorted(successes, key=lambda x: x["thread"]):
            print(f"  {r['thread']:<8} {r['status']:<8} {r['elapsed_s']:<10} "
                  f"{str(r['balance']):<14} {str(r['equity']):<14} "
                  f"{r['open_positions']:<10} {r['deals_history']}")

        times = [r["elapsed_s"] for r in successes]
        print(f"\n  Avg: {sum(times)/len(times):.3f}s  |  Min: {min(times):.3f}s  |  Max: {max(times):.3f}s")

    if failures:
        print(f"\n✗ Failed ({len(failures)}/{NUM_THREADS}):\n")
        for e in sorted(failures, key=lambda x: x["thread"]):
            print(f"  Thread {e['thread']:>2} | status={e['status']} | {e['elapsed_s']}s | {e['error'][:120]}")

    print("\n" + "=" * 60)
    print(f"  Total success: {len(successes)}  |  Total failed: {len(failures)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
