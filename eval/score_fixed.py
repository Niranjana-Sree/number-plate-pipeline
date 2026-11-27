# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import csv, sys
sys.path.insert(0, _os.path.join(ROOT, 'scripts'))
from fix_state import fix_state

rows = list(csv.DictReader(open(_os.path.join(ROOT, 'eval.csv'), encoding="utf-8-sig")))
veh = [r for r in rows if r["vehicle_ok"] == "yes"]
full = [r for r in veh if r["plate_visible"] == "full" and r["human_plate"]]
before = sum(1 for r in full if r["model_plate"].upper() == r["human_plate"])
after = sum(1 for r in full if fix_state(r["model_plate"]) == r["human_plate"])
print(f"fully visible plates: {len(full)}")
print(f"exact match before the TN rule: {before} ({before / max(len(full), 1) * 100:.0f}%)")
print(f"exact match after the TN rule:  {after} ({after / max(len(full), 1) * 100:.0f}%)")
print(f"end to end before: {before} of {len(veh)} ({before / max(len(veh), 1) * 100:.0f}%)")
print(f"end to end after:  {after} of {len(veh)} ({after / max(len(veh), 1) * 100:.0f}%)")
for r in full:
    f = fix_state(r["model_plate"])
    if f != r["model_plate"].upper():
        print("  changed:", r["model_plate"], "->", f, "| real:", r["human_plate"])