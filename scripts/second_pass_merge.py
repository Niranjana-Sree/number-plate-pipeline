import csv, json, os, re, sys
MAP, RES, PAIRS, OUT = sys.argv[1:5]
MIN_PLATE_W = 30
MIN_ASPECT, MAX_ASPECT = 1.2, 6.0
MAX_CROP_AREA = 0.15
cmap = {r["crop_file"]: r for r in csv.DictReader(open(MAP, encoding="utf-8-sig"))}
fields = ["image_file", "status", "source", "vehicle_id", "vehicle_label", "vx1", "vy1", "vx2", "vy2",
          "plate_id", "px1", "py1", "px2", "py2", "plate_width"]
out = []
for r in csv.DictReader(open(PAIRS, encoding="utf-8-sig")):
    if r["status"] == "ok":
        d = {k: r.get(k, "") for k in fields}
        d["source"] = "full_frame"
        out.append(d)
n_ok = n_none = 0
for line in open(RES, encoding="utf-8"):
    if not line.startswith("{"):
        continue
    rec = json.loads(line)
    m = cmap.get(os.path.basename(rec["image"]))
    if not m:
        continue
    x0, y0, cw, ch = float(m["x0"]), float(m["y0"]), float(m["crop_w"]), float(m["crop_h"])
    cands, notes = [], []
    for b in re.findall(r"<box><(\d+)><(\d+)><(\d+)><(\d+)></box>", rec["raw_response"]):
        n = [int(v) for v in b]
        bx = [x0 + n[0] * cw / 1000, y0 + n[1] * ch / 1000, x0 + n[2] * cw / 1000, y0 + n[3] * ch / 1000]
        w, h = bx[2] - bx[0], bx[3] - bx[1]
        share = (w * h) / (cw * ch) if cw * ch else 1
        why = ""
        if w < MIN_PLATE_W: why = "too_narrow"
        elif not (MIN_ASPECT <= w / max(h, 1e-6) <= MAX_ASPECT): why = "odd_shape"
        elif share > MAX_CROP_AREA: why = "whole_crop"
        notes.append("%dx%d %s" % (w, h, why or "ok"))
        if not why:
            cands.append((w, bx))
    base = {"image_file": m["image_file"], "source": "crop_search", "vehicle_id": m["vehicle_id"],
            "vehicle_label": m["vehicle_label"], "vx1": m["vx1"], "vy1": m["vy1"], "vx2": m["vx2"], "vy2": m["vy2"]}
    if cands:
        w, bx = max(cands, key=lambda c: c[0])
        base.update(status="ok", plate_id="C1", px1=round(bx[0], 1), py1=round(bx[1], 1), px2=round(bx[2], 1), py2=round(bx[3], 1), plate_width=round(w, 1))
        n_ok += 1
    else:
        base["status"] = "no_plate_found"; n_none += 1
    out.append(base)
    print(m["crop_file"], "->", base["status"], "|", "; ".join(notes) or "no boxes")
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(out)
print("first-pass pairs:", sum(1 for r in out if r["source"] == "full_frame"), "| crop-search plates found:", n_ok, "| none:", n_none, "| saved:", OUT)