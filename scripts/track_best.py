import csv, os, re, shutil, sys
import numpy as np
from PIL import Image
IMG_DIR, CSV_IN, OUT_CSV, BEST_DIR = sys.argv[1:5]
MAX_GAP = 3
MAX_DY = 0.30
DX_LEFT, DX_RIGHT = 1.5, 0.3
PAD = 0.20

def frame_no(name):
    m = re.findall(r"(\d+)", os.path.splitext(name)[0])
    return int(m[-1]) if m else 0

def crop_plate(r):
    im = Image.open(os.path.join(IMG_DIR, r["image_file"])).convert("RGB")
    x1, y1, x2, y2 = [float(r[k]) for k in ("px1", "py1", "px2", "py2")]
    w, h = x2 - x1, y2 - y1
    return im.crop((int(max(0, x1 - PAD * w)), int(max(0, y1 - PAD * h)), int(min(im.width, x2 + PAD * w)), int(min(im.height, y2 + PAD * h))))

def sharpness(img):
    img = img.convert("L")
    img = img.resize((200, max(8, int(200 * img.height / img.width))), Image.LANCZOS)
    g = np.asarray(img, dtype=np.float64)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())

rows = [r for r in csv.DictReader(open(CSV_IN, encoding="utf-8-sig")) if r["status"] == "ok"]
for r in rows:
    r["_f"] = frame_no(r["image_file"])
    r["_cx"] = (float(r["vx1"]) + float(r["vx2"])) / 2
    r["_cy"] = (float(r["vy1"]) + float(r["vy2"])) / 2
    r["_w"] = float(r["vx2"]) - float(r["vx1"])
    r["_h"] = float(r["vy2"]) - float(r["vy1"])
rows.sort(key=lambda r: (r["_f"], r["vehicle_id"]))
tracks = []
for r in rows:
    best, bd = None, None
    for t in tracks:
        last = t[-1]
        gap = r["_f"] - last["_f"]
        if gap < 1 or gap > MAX_GAP:
            continue
        dx = r["_cx"] - last["_cx"]
        dy = abs(r["_cy"] - last["_cy"])
        if dy > MAX_DY * last["_h"] or dx < -DX_LEFT * gap * last["_w"] or dx > DX_RIGHT * last["_w"]:
            continue
        d = abs(dx) + dy
        if bd is None or d < bd:
            best, bd = t, d
    if best is None:
        tracks.append([r])
    else:
        best.append(r)
os.makedirs(BEST_DIR, exist_ok=True)
fields = ["track_id", "n_frames", "first_frame", "last_frame", "vehicle_label", "best_image", "best_sharpness", "plate_width",
          "vx1", "vy1", "vx2", "vy2", "px1", "py1", "px2", "py2", "best_crop"]
out = []
for i, t in enumerate(tracks, 1):
    scored = []
    for r in t:
        c = crop_plate(r)
        scored.append((sharpness(c), r, c))
    s, r, c = max(scored, key=lambda x: x[0])
    labels = [x["vehicle_label"] for x in t]
    lab = max(set(labels), key=labels.count)
    cf = "track_%02d_%s.png" % (i, os.path.splitext(r["image_file"])[0])
    c.save(os.path.join(BEST_DIR, cf))
    out.append({"track_id": "T%02d" % i, "n_frames": len(t), "first_frame": t[0]["_f"], "last_frame": t[-1]["_f"], "vehicle_label": lab,
                "best_image": r["image_file"], "best_sharpness": round(s, 1), "plate_width": r["plate_width"],
                "vx1": r["vx1"], "vy1": r["vy1"], "vx2": r["vx2"], "vy2": r["vy2"],
                "px1": r["px1"], "py1": r["py1"], "px2": r["px2"], "py2": r["py2"], "best_crop": cf})
    print("T%02d | frames %s | %s | best %s sharp %.0f" % (i, ",".join(str(x["_f"]) for x in t), lab, r["image_file"], s))
with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(out)
print("appearances:", len(rows), "| distinct vehicles:", len(tracks), "| saved:", OUT_CSV)