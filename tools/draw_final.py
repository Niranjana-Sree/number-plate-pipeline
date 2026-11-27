import csv, os, sys
from PIL import Image, ImageDraw
IMG_DIR, CSV_IN, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
by = {}
for r in csv.DictReader(open(CSV_IN, encoding="utf-8-sig")):
    if r["status"] == "ok":
        by.setdefault(r["image_file"], []).append(r)
for name, rs in sorted(by.items()):
    im = Image.open(os.path.join(IMG_DIR, name)).convert("RGB")
    W = im.width
    d = ImageDraw.Draw(im)
    w = max(4, W // 400)
    for r in rs:
        d.rectangle([float(r[k]) for k in ("vx1", "vy1", "vx2", "vy2")], outline=(0, 255, 0), width=w)
        p = [float(r[k]) for k in ("px1", "py1", "px2", "py2")]
        pw, ph = p[2] - p[0], p[3] - p[1]
        p = [p[0] - 0.15 * pw, p[1] - 0.15 * ph, p[2] + 0.15 * pw, p[3] + 0.15 * ph]
        d.rectangle(p, outline=(255, 0, 0), width=max(2, w // 2))
        tag = "%s %s plate %dpx (%s)" % (r["vehicle_id"], r["vehicle_label"], float(r["plate_width"]), "crop" if r["source"] == "crop_search" else "full")
        d.text((float(r["vx1"]) + 8, float(r["vy1"]) + 8), tag, fill=(0, 255, 0))
    im.thumbnail((1600, 1600))
    im.save(os.path.join(OUT, "fin_" + name))
print("frames drawn:", len(by), "| vehicle+plate pairs:", sum(len(v) for v in by.values()), "->", OUT)