# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import csv, os, re, sys
sys.path.insert(0, _os.path.join(ROOT, 'scripts'))
from fix_state import fix_state, clean

lab = {os.path.basename(r["best_crop_path"]): r for r in csv.DictReader(open(_os.path.join(ROOT, 'eval.csv'), encoding="utf-8-sig"))}
test1 = {r["crop_file"]: r for r in csv.DictReader(open(_os.path.join(ROOT, 'eval_crops_test.csv'), encoding="utf-8-sig"))}
test2 = {r["crop_file"]: r for r in csv.DictReader(open(_os.path.join(ROOT, 'eval_crops_test2.csv'), encoding="utf-8-sig"))}
PAT = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$")
full = [f for f, l in lab.items() if l["vehicle_ok"] == "yes" and l["plate_visible"] == "full" and l["human_plate"] and f in test2]
none = [f for f, l in lab.items() if l["vehicle_ok"] == "yes" and l["plate_visible"] == "none" and f in test2]
print(f"readable plates: {len(full)} | unreadable crops: {len(none)}")
cols = [("A_base (original)", test1, "A_base"), ("B_format_hint", test1, "B_format_hint"),
        ("D_hint_unreadable", test2, "D_hint_unreadable"), ("E_base_unreadable", test2, "E_base_unreadable"), ("G_gate", test2, "G_gate")]
for name, src, col in cols:
    ok = sum(1 for f in full if fix_state(src[f][col]) == lab[f]["human_plate"])
    rej = sum(1 for f in full if src[f][col] == "UNREADABLE")
    good = sum(1 for f in none if src[f][col] == "UNREADABLE")
    fake = sum(1 for f in none if PAT.match(fix_state(src[f][col])))
    print(f"{name}: readable exact(with TN rule) {ok}/{len(full)} | readable wrongly rejected {rej} | "
          f"unreadable correctly rejected {good}/{len(none)} | unreadable with a valid-looking invented plate {fake}/{len(none)}")