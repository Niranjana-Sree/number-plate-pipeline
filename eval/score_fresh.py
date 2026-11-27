# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import csv, os, re, sys
sys.path.insert(0, _os.path.join(ROOT, 'scripts'))
from fix_state import fix_state, clean

old = set(os.listdir(_os.path.join(ROOT, 'eval_crops')))
lab = {}
for r in csv.DictReader(open(_os.path.join(ROOT, 'eval.csv'), encoding="utf-8-sig")):
    f = os.path.basename(r["best_crop_path"])
    if f not in old and r["vehicle_ok"] == "yes":
        lab[f] = r
A = {r["crop_file"]: r["plate_text"] for r in csv.DictReader(open(_os.path.join(ROOT, 'eval_fresh_A.csv'), encoding="utf-8-sig"))}
PAT = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$")
full = [f for f, l in lab.items() if l["plate_visible"] == "full" and l["human_plate"]]
part = [f for f, l in lab.items() if l["plate_visible"] == "partial"]
none = [f for f, l in lab.items() if l["plate_visible"] == "none"]
print(f"fresh vehicles: {len(lab)} | full {len(full)} | partial {len(part)} | none {len(none)}")


def report(name, get):
    ok = sum(1 for f in full if get(f) == lab[f]["human_plate"])
    rej_full = sum(1 for f in full if get(f) == "")
    rej_none = sum(1 for f in none if get(f) == "")
    fake = sum(1 for f in none if PAT.match(get(f) or ""))
    rej_part = sum(1 for f in part if get(f) == "")
    print(f"{name}: readable exact {ok}/{len(full)} | readable rejected {rej_full} | "
          f"unreadable rejected {rej_none}/{len(none)} | unreadable with valid-looking plate {fake}/{len(none)} | "
          f"partial rejected {rej_part}/{len(part)}")


report("D (pipeline, with TN rule)", lambda f: clean(lab[f]["model_plate"]))
report("A (original prompt + TN rule)", lambda f: fix_state(A.get(f, "")))