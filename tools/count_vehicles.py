import csv, os, collections

def rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

if os.path.exists("all_results.csv"):
    r = rows("all_results.csv")
    print("columns:", list(r[0].keys()) if r else "none")
    chunks = collections.Counter(x.get("chunk", "?") for x in r)
    print(f"\nall_results.csv: {len(r)} rows, {len(chunks)} chunks")
    for c, n in sorted(chunks.items()):
        print(f"  {c}: {n}")

if os.path.exists("eval.csv"):
    e = rows("eval.csv")
    print(f"\neval.csv (labelled): {len(e)} vehicles")
    print("  vehicle real yes:", sum(x["vehicle_ok"].strip().lower() == "yes" for x in e))
    print("  visibility:", dict(collections.Counter(x["plate_visible"] for x in e)))
    print("  chunks labelled:", len(set(x["chunk"] for x in e)))