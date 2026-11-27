import csv, json, os, sys
from PIL import Image, ImageDraw
IMG_DIR, CSV_IN, ROI, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(OUT, exist_ok=True)
poly = json.load(open(ROI))
by = {}
for r in csv.DictReader(open(CSV_IN, encoding="utf-8-sig")):
    if r["kind"] == "vehicle":
        by.setdefault(r["image_file"], []).append(r)
n = 0
for name, rs in sorted(by.items()):
    show = [r for r in rs if r["drop_reason"] != "cut_off_bottom"]
    if not show:
        continue
    im = Image.open(os.path.join(IMG_DIR, name)).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    w = max(4, W // 400)
    d.polygon([(a * W, b * H) for a, b in poly], outline=(0, 120, 255), width=w)
    for r in show:
        kept = r["kept"] == "True"
        col = (0, 255, 0) if kept else (255, 140, 0)
        box = [float(r[k]) for k in ("x1", "y1", "x2", "y2")]
        d.rectangle(box, outline=col, width=w)
        d.text((box[0] + 6, box[1] + 6), "%s %s %s" % (r["object_id"], r["label"], "KEPT" if kept else r["drop_reason"]), fill=col)
    im.thumbnail((1600, 1600))
    im.save(os.path.join(OUT, "chk_" + name))
    n += 1
    print(name, "kept:", sum(1 for r in show if r["kept"] == "True"), "| dropped:", sum(1 for r in show if r["kept"] != "True"))
print("images saved:", n, "->", OUT)