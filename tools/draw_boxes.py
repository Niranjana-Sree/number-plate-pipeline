import json
import re
import sys
import cv2
import numpy as np

if len(sys.argv) != 3:
    print("usage: python draw_boxes.py <result.jsonl> <output.jpg>")
    sys.exit(1)

RESULT, OUT = sys.argv[1], sys.argv[2]
SCALE = 1000  # assumption: model coordinates are on a 0-1000 scale

with open(RESULT, encoding="utf-8") as f:
    rec = json.loads(f.readline())

print("reading:", RESULT)
print("query:", rec["query"])

img = cv2.imdecode(np.fromfile(rec["image"], dtype=np.uint8), cv2.IMREAD_COLOR)
H, W = img.shape[:2]
print("image size:", W, "x", H)

colors = {
    "car": (0, 200, 0),
    "truck": (255, 120, 0),
    "bus": (200, 0, 200),
    "motorcycle": (0, 200, 200),
    "bicycle": (0, 140, 255),
    "number plate": (0, 0, 255),
    "license plate": (0, 0, 255),
}

thick = max(2, W // 400)
font_scale = max(0.5, W / 1800)

parts = re.split(r"<ref>(.*?)</ref>", rec["raw_response"])
n = 0
print("no | label | model box | pixel box | width px | area % of image")
for i in range(1, len(parts), 2):
    label, body = parts[i], parts[i + 1]
    for m in re.finditer(r"<box>((?:<\d+>){4})</box>", body):
        x1, y1, x2, y2 = [int(v) for v in re.findall(r"<(\d+)>", m.group(1))]
        px1, py1 = int(x1 / SCALE * W), int(y1 / SCALE * H)
        px2, py2 = int(x2 / SCALE * W), int(y2 / SCALE * H)
        area = (px2 - px1) * (py2 - py1) / (W * H) * 100
        n += 1
        print(f"{n} | {label} | {x1},{y1},{x2},{y2} | {px1},{py1},{px2},{py2} | {px2 - px1} | {area:.2f}")
        color = colors.get(label, (255, 255, 255))
        cv2.rectangle(img, (px1, py1), (px2, py2), color, thick)
        cv2.putText(img, f"{n} {label}", (px1, max(py1 - 5, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thick)

cv2.imencode(".jpg", img)[1].tofile(OUT)
print("saved:", OUT)