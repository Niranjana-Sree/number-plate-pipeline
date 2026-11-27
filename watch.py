import csv, datetime, glob, os, sys, time
import pipeline

CHUNKS = os.path.join(pipeline.ROOT, "chunks")
MASTER = os.path.join(pipeline.ROOT, "all_results.csv")
SETTLE_SEC = 90
POLL_SEC = 30


def statuses(): # for finished status
    if not os.path.exists(pipeline.STATUS):
        return {}
    return {r["chunk"]: r["status"] for r in csv.DictReader(open(pipeline.STATUS, encoding="utf-8-sig"))}


def abs_time(chunk, secs): # for logging time
    try:
        d = datetime.datetime.strptime(chunk.split("cam_")[1], "%Y%m%d_%H%M%S")
        return (d + datetime.timedelta(seconds=float(secs))).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def append_master(chunk): # append a cam vid result to global result
    src = os.path.join(pipeline.WORK, chunk, "result.csv") # result of current video from pipeline
    if not os.path.exists(src):
        return 0
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    if not rows:
        return 0
    for r in rows:
        r["abs_time"] = abs_time(chunk, r["best_time_s"] or r["time_in_chunk_s"])
    new = not os.path.exists(MASTER)
    with open(MASTER, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if new:
            w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    once = "--once" in sys.argv
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10**9
    count = 0
    while count < limit:
        st = statuses()
        todo = []
        for f in sorted(glob.glob(os.path.join(CHUNKS, "cam_*.mkv"))):
            name = os.path.splitext(os.path.basename(f))[0]
            if name in st and st[name] in ("done", "failed"):
                continue
            if time.time() - os.path.getmtime(f) < SETTLE_SEC:
                continue
            todo.append((name, f))
        if todo:
            name, f = todo[0]
            print("=== chunk:", name, flush=True)
            pipeline.process(f)
            count += 1
            if statuses().get(name) == "done":
                print("   rows added to all_results.csv:", append_master(name), flush=True)
            continue
        if once: # process what is availbale dont wait for poll sec
            break
        time.sleep(POLL_SEC)
    print("watcher finished. chunks processed this run:", count)


if __name__ == "__main__":
    main()