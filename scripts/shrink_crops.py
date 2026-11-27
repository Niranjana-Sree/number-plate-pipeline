import json, os, sys
from PIL import Image

D = sys.argv[1]
MAX_SIDE = 1280
small = os.path.join(D, "small")
os.makedirs(small, exist_ok=True)
out = []
for line in open(os.path.join(D, "crop_requests.jsonl"), encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    src = r["image"]
    im = Image.open(src)
    w, h = im.size
    s = MAX_SIDE / max(w, h)
    if s < 1:
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    dst = os.path.join(small, os.path.basename(src))
    im.save(dst)
    r["image"] = dst
    out.append(r)
with open(os.path.join(D, "crop_requests_small.jsonl"), "w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("crops:", len(out), "| longest side capped at", MAX_SIDE)