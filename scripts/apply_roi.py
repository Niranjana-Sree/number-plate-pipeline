import csv, json, sys
IN, ROI, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BOTTOM_TOL = 0.01
EDGE_TOL = 0.01
SIDE_MIN_W = 0.15
poly = json.load(open(ROI))

def inside(px, py, pts):
    ok = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            ok = not ok
        j = i
    return ok

rows = list(csv.DictReader(open(IN, encoding="utf-8-sig")))
n_out = n_cut = n_side = n_keep = 0
for r in rows:
    if r["kind"] != "vehicle" or r["kept"] != "True":
        continue
    W, H = float(r["image_w"]), float(r["image_h"])
    fx = (float(r["x1"]) + float(r["x2"])) / 2 / W
    fy = float(r["y2"]) / H
    if float(r["y2"]) >= H * (1 - BOTTOM_TOL):
        r["kept"], r["drop_reason"] = "False", "cut_off_bottom"; n_cut += 1
    elif float(r["x2"]) >= W * (1 - EDGE_TOL) or (float(r["x1"]) <= W * EDGE_TOL and (float(r["x2"]) - float(r["x1"])) < W * SIDE_MIN_W):
        r["kept"], r["drop_reason"] = "False", "cut_off_side"; n_side += 1
    elif not inside(fx, fy, poly):
        r["kept"], r["drop_reason"] = "False", "outside_roi"; n_out += 1
    else:
        n_keep += 1
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("vehicles kept:", n_keep, "| outside_roi:", n_out, "| cut_off_bottom:", n_cut, "| cut_off_side:", n_side, "| saved:", OUT)