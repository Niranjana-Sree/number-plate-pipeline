# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import csv, os, sys
sys.path.insert(0, _os.path.join(ROOT, 'scripts'))
from fix_state import fix_state, clean

lab = {os.path.basename(r["best_crop_path"]): r for r in csv.DictReader(open(_os.path.join(ROOT, 'eval.csv'), encoding="utf-8-sig"))}
rows = list(csv.DictReader(open(_os.path.join(ROOT, 'eval_crops_test.csv'), encoding="utf-8-sig")))
full = []
for r in rows:
    l = lab.get(r["crop_file"])
    if l and l["vehicle_ok"] == "yes" and l["plate_visible"] == "full" and l["human_plate"]:
        full.append((r, l))
n = len(full)
old = sum(1 for r, l in full if clean(l["model_plate"]) == l["human_plate"])
oldf = sum(1 for r, l in full if fix_state(l["model_plate"]) == l["human_plate"])
print(f"fully readable plates: {n}")
print(f"pipeline (original reading): exact {old}/{n} | with TN rule {oldf}/{n}")
for col in ("A_base", "B_format_hint", "C_sharpen"):
    raw = sum(1 for r, l in full if clean(r[col]) == l["human_plate"])
    fx = sum(1 for r, l in full if fix_state(r[col]) == l["human_plate"])
    print(f"{col}: exact {raw}/{n} | with TN rule {fx}/{n}")