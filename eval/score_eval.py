# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import csv, collections

P = _os.path.join(ROOT, 'eval.csv')
rows = list(csv.DictReader(open(P, encoding="utf-8-sig")))


def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


n = len(rows)
veh = [r for r in rows if r["vehicle_ok"] == "yes"]
vis = collections.Counter(r["plate_visible"] for r in veh)
print("=== VEHICLE DETECTION ===")
print(f"vehicles checked: {n} | real vehicles: {len(veh)} | precision: {len(veh) / n * 100:.0f}%")
print("(recall, vehicles the model missed, is not measured here)")

print("\n=== PLATE VISIBILITY (human, among real vehicles) ===")
for k in ("full", "partial", "none"):
    print(f"{k}: {vis[k]} ({vis[k] / max(len(veh), 1) * 100:.0f}%)")

full = [r for r in veh if r["plate_visible"] == "full" and r["human_plate"]]
print("\n=== PLATE READING, fully visible plates ===")
if full:
    exact = [r for r in full if r["model_plate"].upper() == r["human_plate"]]
    acc = [max(0.0, 1 - lev(r["model_plate"].upper(), r["human_plate"]) / max(len(r["human_plate"]), 1)) for r in full]
    print(f"plates: {len(full)} | exact match: {len(exact)} ({len(exact) / len(full) * 100:.0f}%)")
    print(f"average character accuracy: {sum(acc) / len(acc) * 100:.0f}%")
    wrong = [r for r in full if r not in exact]
    caught = [r for r in wrong if r["format_status"] != "valid"]
    print(f"wrong reads: {len(wrong)} | flagged by the format check: {len(caught)}")
    for r in wrong:
        print(f"   model {r['model_plate']} vs real {r['human_plate']} [{r['format_status']}]")
else:
    print("no fully visible plates labelled")

part = [r for r in veh if r["plate_visible"] == "partial"]
print("\n=== PARTLY VISIBLE PLATES ===")
agree = [r for r in part if r["human_plate"] and r["model_plate"] and
         (r["human_plate"] in r["model_plate"].upper() or r["model_plate"].upper() in r["human_plate"])]
print(f"plates: {len(part)} | model text agrees with the visible part: {len(agree)}")

none = [r for r in veh if r["plate_visible"] == "none"]
inv = [r for r in none if r["model_plate"]]
print("\n=== UNREADABLE PLATES ===")
print(f"plates: {len(none)} | model still gave text: {len(inv)} | of those flagged by the format check: {sum(1 for r in inv if r['format_status'] != 'valid')}")

ok_all = sum(1 for r in full if r["model_plate"].upper() == r["human_plate"])
print("\n=== END TO END ===")
print(f"correct plate for {ok_all} of {len(veh)} real vehicles ({ok_all / max(len(veh), 1) * 100:.0f}%)")