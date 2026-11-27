import csv, os, sys, collections
BASE = os.path.expanduser("~/locate-work/ccpd10k")
IN = sys.argv[1] if len(sys.argv) > 1 else BASE + "/detections_pilot200.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else BASE + "/final_pairs_pilot200.csv"
MARGIN = 0.40     # plate centre may sit this fraction of the vehicle height below the vehicle box
MAX_PAIRS = 5     # vehicle+plate pairs kept per image
rows = list(csv.DictReader(open(IN, encoding="utf-8-sig")))
by = collections.OrderedDict()
for r in rows: by.setdefault(r["image_file"], []).append(r)
fields = ["image_file", "status", "vehicle_id", "vehicle_label", "vx1", "vy1", "vx2", "vy2",
          "plate_id", "px1", "py1", "px2", "py2", "plate_width", "plate_below_vehicle_pct",
          "is_label_plate", "iou_with_label"]
out, ok, none, labeled, margin_used = [], 0, [], 0, 0
vlabels, ious, wrong = collections.Counter(), [], []
for name, rs in by.items():
    vs = [r for r in rs if r["kind"] == "vehicle" and r["kept"] == "True"]
    ps = [r for r in rs if r["kind"] == "plate" and r["drop_reason"] in ("", "no_vehicle")]
    cands = []
    for p in ps:
        cx = (float(p["x1"]) + float(p["x2"])) / 2
        cy = (float(p["y1"]) + float(p["y2"])) / 2
        best = None
        for v in vs:
            x1, y1, x2, y2 = [float(v[k]) for k in ("x1", "y1", "x2", "y2")]
            h = y2 - y1
            if x1 <= cx <= x2 and y1 <= cy <= y2 + MARGIN * h:
                a = (x2 - x1) * h
                if best is None or a < best[0]:
                    best = (a, v, 100 * max(0.0, cy - y2) / h)
        if best: cands.append((float(p["box_w"]), p, best[1], best[2]))
    cands.sort(key=lambda c: -c[0])
    if not cands:
        out.append({"image_file": name, "status": "no_valid_pair"})
        none.append(name[10:30])
        continue
    for w, p, v, below in cands[:MAX_PAIRS]:
        ok += 1
        out.append({"image_file": name, "status": "ok", "vehicle_id": v["object_id"], "vehicle_label": v["label"],
                    "vx1": v["x1"], "vy1": v["y1"], "vx2": v["x2"], "vy2": v["y2"],
                    "plate_id": p["object_id"], "px1": p["x1"], "py1": p["y1"], "px2": p["x2"], "py2": p["y2"],
                    "plate_width": p["box_w"], "plate_below_vehicle_pct": round(below, 1),
                    "is_label_plate": p["is_label_plate"], "iou_with_label": p["iou_with_label"]})
        vlabels[v["label"]] += 1
        if below > 0: margin_used += 1
        if p["is_label_plate"] == "yes":
            labeled += 1
            ious.append(float(p["iou_with_label"]))
        else:
            wrong.append(name[10:30])
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(out)
print("images:", len(by), "| pairs found:", ok, "| no_valid_pair:", len(none))
print("chosen plate is the labeled plate:", labeled, "of", ok, "| chosen plate NOT the labeled one:", len(wrong))
print("pairs that needed the below-the-box margin:", margin_used)
print("vehicle labels chosen:", dict(vlabels))
if ious: print("IoU of chosen plates: >=0.75:", sum(1 for v in ious if v >= 0.75), "of", len(ious), "| mean %.3f" % (sum(ious) / len(ious)))
print("images with no valid pair:", none)
print("images where a wrong plate was chosen:", wrong)
print("saved:", OUT)
