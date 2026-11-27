import csv, json, os, sys
from PIL import Image
IMG_DIR, ROI_CSV, PAIRS, OUT = sys.argv[1:5]
PAD = 0.15
QUERY = "vehicle registration plate"
os.makedirs(OUT, exist_ok=True)
paired = set()
for r in csv.DictReader(open(PAIRS, encoding="utf-8-sig")):
    if r["status"] == "ok":
        paired.add((r["image_file"], r["vehicle_id"]))
todo = [r for r in csv.DictReader(open(ROI_CSV, encoding="utf-8-sig"))
        if r["kind"] == "vehicle" and r["kept"] == "True" and (r["image_file"], r["object_id"]) not in paired]
mp = open(os.path.join(OUT, "crop_map.csv"), "w", newline="", encoding="utf-8-sig")
mw = csv.writer(mp)
mw.writerow(["crop_file", "image_file", "vehicle_id", "vehicle_label", "x0", "y0", "crop_w", "crop_h", "vx1", "vy1", "vx2", "vy2"])
req = open(os.path.join(OUT, "crop_requests.jsonl"), "w", encoding="utf-8")
cache = {}
for r in todo:
    name = r["image_file"]
    if name not in cache:
        cache = {name: Image.open(os.path.join(IMG_DIR, name)).convert("RGB")}
    im = cache[name]
    x1, y1, x2, y2 = [float(r[k]) for k in ("x1", "y1", "x2", "y2")]
    w, h = x2 - x1, y2 - y1
    box = [max(0, x1 - PAD * w), max(0, y1 - PAD * h), min(im.width, x2 + PAD * w), min(im.height, y2 + PAD * h)]
    box = [int(v) for v in box]
    cf = os.path.splitext(name)[0] + "_" + r["object_id"] + ".png"
    cp = os.path.abspath(os.path.join(OUT, cf))
    im.crop(tuple(box)).save(cp)
    req.write(json.dumps({"image": cp, "query": QUERY}) + "\n")
    mw.writerow([cf, name, r["object_id"], r["label"], box[0], box[1], box[2] - box[0], box[3] - box[1], x1, y1, x2, y2])
mp.close(); req.close()
print("vehicles without a plate pair:", len(todo), "->", OUT)