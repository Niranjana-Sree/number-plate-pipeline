import json, re, csv, os, sys
from PIL import Image
D = "/media/mlteam/One Touch/Backup_Data/lp/ccpd/train"
BASE = os.path.expanduser("~/locate-work/ccpd10k")
RES = sys.argv[1] if len(sys.argv) > 1 else BASE + "/results_pilot200.jsonl"
OUT = sys.argv[2] if len(sys.argv) > 2 else BASE + "/detections_pilot200.csv"
MIN_PLATE_W = 30      # plates narrower than this (pixels) are marked far_plate
MIN_VEH_PCT = 1.0    # vehicle boxes below this % of the image are marked too_small
IOU_THR = 0.5         # same-kind boxes overlapping more than this are duplicates
area = lambda b: max(0, b[2]-b[0]) * max(0, b[3]-b[1])
def iou(a, b):
    i = area([max(a[0],b[0]), max(a[1],b[1]), min(a[2],b[2]), min(a[3],b[3])])
    u = area(a) + area(b) - i
    return i / u if u else 0.0
def dedupe(items):
    kept = []
    for d in sorted(items, key=lambda d: area(d["box"]), reverse=True):
        if any(iou(d["box"], k["box"]) >= IOU_THR for k in kept):
            d["reason"] = "duplicate"
        else:
            kept.append(d)
fields = ["image_file","image_w","image_h","object_id","kind","label","kept","drop_reason",
          "x1","y1","x2","y2","box_w","box_h","area_pct","x1_n","y1_n","x2_n","y2_n",
          "matched_vehicle_id","plates_assigned","has_plate","is_label_plate","iou_with_label",
          "gt_x1","gt_y1","gt_x2","gt_y2"]
rows, extras, best_ious = [], [], []
flag_label = {}
vstat = {"kept": 0, "too_small": 0, "duplicate": 0, "with_plate": 0, "without_plate": 0}
n_img = 0
for line in open(RES):
    if not line.startswith("{"): continue
    rec = json.loads(line)
    name = os.path.basename(rec["image"])
    W, H = Image.open(rec["image"]).size
    n_img += 1
    vs, ps = [], []
    for m in re.finditer(r"<ref>(.*?)</ref>((?:<box>.*?</box>)*)", rec["raw_response"]):
        lab = m.group(1).strip()
        for b in re.findall(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>", m.group(2)):
            n = [int(v) for v in b]
            d = {"label": lab, "norm": n, "box": [n[0]*W/1000, n[1]*H/1000, n[2]*W/1000, n[3]*H/1000],
                 "reason": "", "match": "", "plates": "", "has_plate": "", "is_label": "", "iou": ""}
            (ps if "plate" in lab.lower() else vs).append(d)
    for i, d in enumerate(vs, 1): d["id"] = "V%d" % i; d["kind"] = "vehicle"
    for j, d in enumerate(ps, 1): d["id"] = "P%d" % j; d["kind"] = "plate"
    for d in vs + ps: d["pct"] = 100.0 * area(d["box"]) / (W * H)
    for d in vs:
        if d["pct"] < MIN_VEH_PCT: d["reason"] = "too_small"
    dedupe([d for d in vs if not d["reason"]])
    for p in ps:
        if p["box"][2] - p["box"][0] < MIN_PLATE_W: p["reason"] = "far_plate"
    dedupe([p for p in ps if not p["reason"]])
    kv = [v for v in vs if not v["reason"]]
    for p in ps:
        if p["reason"]: continue
        cx, cy = (p["box"][0]+p["box"][2])/2, (p["box"][1]+p["box"][3])/2
        c = [v for v in kv if v["box"][0] <= cx <= v["box"][2] and v["box"][1] <= cy <= v["box"][3]]
        if c: p["match"] = min(c, key=lambda v: area(v["box"]))["id"]
        else: p["reason"] = "no_vehicle"
    kp = [p for p in ps if not p["reason"]]
    for v in kv:
        v["plates"] = ";".join(p["id"] for p in kp if p["match"] == v["id"])
        v["has_plate"] = "yes" if v["plates"] else "no"
        vstat["with_plate" if v["plates"] else "without_plate"] += 1
    for v in vs:
        vstat["kept" if not v["reason"] else v["reason"]] += 1
    gt = None
    lp = D + "/labels2/" + os.path.splitext(name)[0] + ".txt"
    if os.path.exists(lp):
        ls = [l.split() for l in open(lp) if l.strip()]
        if ls:
            v8 = [float(x) for x in ls[0][1:9]]
            xs, ys = [v8[i]*W for i in range(0, 8, 2)], [v8[i]*H for i in range(1, 8, 2)]
            gt = [min(xs), min(ys), max(xs), max(ys)]
    if gt and ps:
        for p in ps: p["iou"] = iou(p["box"], gt)
        best = max(ps, key=lambda p: p["iou"])
        best_ious.append(best["iou"])
        for p in ps:
            p["is_label"] = "yes" if (p is best and p["iou"] >= 0.5) else "no"
            if p["is_label"] == "yes" and p["reason"]:
                flag_label[p["reason"]] = flag_label.get(p["reason"], 0) + 1
            if p["is_label"] == "no":
                extras.append((n_img, name[10:28], round(p["box"][2]-p["box"][0]), p["reason"] or "kept_ok", round(p["iou"], 2)))
    for d in vs + ps:
        b = d["box"]
        r = {"image_file": name, "image_w": W, "image_h": H, "object_id": d["id"], "kind": d["kind"],
             "label": d["label"], "kept": "True" if not d["reason"] else "False", "drop_reason": d["reason"],
             "x1": round(b[0],1), "y1": round(b[1],1), "x2": round(b[2],1), "y2": round(b[3],1),
             "box_w": round(b[2]-b[0],1), "box_h": round(b[3]-b[1],1), "area_pct": round(d["pct"],2),
             "x1_n": d["norm"][0], "y1_n": d["norm"][1], "x2_n": d["norm"][2], "y2_n": d["norm"][3]}
        if d["kind"] == "plate":
            r["matched_vehicle_id"] = d["match"]
            r["is_label_plate"] = d["is_label"]
            r["iou_with_label"] = round(d["iou"], 3) if d["iou"] != "" else ""
            if gt: r.update(gt_x1=round(gt[0],1), gt_y1=round(gt[1],1), gt_x2=round(gt[2],1), gt_y2=round(gt[3],1))
        else:
            r["plates_assigned"] = d["plates"]
            r["has_plate"] = d["has_plate"]
        rows.append(r)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(rows)
print("images:", n_img, "| labeled plates matched (IoU>=0.5):", sum(1 for v in best_ious if v >= 0.5),
      "| >=0.75:", sum(1 for v in best_ious if v >= 0.75), "| mean best IoU: %.3f" % (sum(best_ious)/max(1, len(best_ious))))
print("labeled plates wrongly flagged by a rule (should be 0):", flag_label or 0)
print("vehicles:", vstat)
print("extra plate boxes (not the labeled plate):", len(extras))
for e in extras: print("  img %d %s... | width %d px | status %s | IoU with label %s" % e)
print("saved:", OUT)
