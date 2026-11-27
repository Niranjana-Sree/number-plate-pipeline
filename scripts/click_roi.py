# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import json, sys, tkinter as tk
from PIL import Image, ImageTk, ImageDraw
src = sys.argv[1]
im = Image.open(src).convert("RGB")
W, H = im.size
S = 1500 / W
disp = im.resize((1500, int(H * S)))
root = tk.Tk()
root.title("Left-click = add corner | Right-click = undo | Enter = save and close")
cv = tk.Canvas(root, width=disp.width, height=disp.height)
cv.pack()
tkimg = ImageTk.PhotoImage(disp)
cv.create_image(0, 0, anchor="nw", image=tkimg)
pts = []
def redraw():
    cv.delete("poly")
    for x, y in pts:
        cv.create_oval(x-4, y-4, x+4, y+4, fill="red", tags="poly")
    if len(pts) > 1:
        cv.create_line(*[c for p in pts for c in p], pts[0][0], pts[0][1], fill="yellow", width=2, tags="poly")
cv.bind("<Button-1>", lambda e: (pts.append((e.x, e.y)), redraw()))
cv.bind("<Button-3>", lambda e: (pts.pop() if pts else None, redraw()))
def save(e=None):
    if len(pts) < 3:
        print("need at least 3 points"); return
    norm = [[round(x / disp.width, 4), round(y / disp.height, 4)] for x, y in pts]
    json.dump(norm, open(_os.path.join(ROOT, 'roi.json'), "w"))
    chk = im.copy(); d = ImageDraw.Draw(chk)
    d.polygon([(a * W, b * H) for a, b in norm], outline="lime", width=8)
    chk.thumbnail((1600, 1600)); chk.save(_os.path.join(ROOT, 'roi_check.jpg'))
    print("saved roi.json with", len(norm), "points")
    root.destroy()
root.bind("<Return>", save)
root.mainloop()