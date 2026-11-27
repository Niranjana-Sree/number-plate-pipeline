# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import csv, glob, os, sys, tkinter as tk
from PIL import Image, ImageDraw, ImageTk

ROOT = ROOT
OUT = os.path.join(ROOT, "eval.csv")
FIELDS = ["chunk", "track_id", "vehicle_label", "model_plate", "format_status",
          "human_plate", "vehicle_ok", "plate_visible", "best_crop_path", "best_image_path"]

rows = []
for p in sorted(glob.glob(os.path.join(ROOT, "work", "cam_*", "result.csv"))):
    rows.extend(csv.DictReader(open(p, encoding="utf-8-sig")))
done = set()
if os.path.exists(OUT):
    for r in csv.DictReader(open(OUT, encoding="utf-8-sig")):
        done.add((r["chunk"], r["track_id"]))
todo = [r for r in rows if (r["chunk"], r["track_id"]) not in done]
if not todo:
    print("Nothing left to check. File:", OUT)
    sys.exit()

root = tk.Tk()
root.title("Plate check")
state = {"i": 0}
img_lbl = tk.Label(root)
img_lbl.grid(row=0, column=0, padx=6, pady=6, sticky="n")
right = tk.Frame(root)
right.grid(row=0, column=1, padx=6, pady=6, sticky="n")
crop_lbl = tk.Label(right)
crop_lbl.pack()
info = tk.Label(right, justify="left", font=("Consolas", 13))
info.pack(pady=6)
tk.Label(right, text="Real plate text (type what you see):").pack(anchor="w")
ent = tk.Entry(right, font=("Consolas", 18), width=16)
ent.pack(anchor="w")
vv = tk.StringVar(value="yes")
tk.Label(right, text="Is the GREEN box a real vehicle?").pack(anchor="w", pady=(8, 0))
for t in ("yes", "no"):
    tk.Radiobutton(right, text=t, variable=vv, value=t).pack(anchor="w")
pv = tk.StringVar(value="full")
tk.Label(right, text="Plate visible in the crop:").pack(anchor="w", pady=(8, 0))
for t in ("full", "partial", "none"):
    tk.Radiobutton(right, text=t, variable=pv, value=t).pack(anchor="w")
prog = tk.Label(right, font=("Consolas", 12))
prog.pack(pady=6)


def frame_img(r):
    im = Image.open(r["best_image_path"]).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle([int(r["vx1"]), int(r["vy1"]), int(r["vx2"]), int(r["vy2"])], outline=(0, 255, 0), width=8)
    d.rectangle([int(r["px1"]), int(r["py1"]), int(r["px2"]), int(r["py2"])], outline=(255, 0, 0), width=6)
    s = 900 / im.width
    return im.resize((900, int(im.height * s)), Image.LANCZOS)


def crop_img(r):
    c = Image.open(r["best_crop_path"]).convert("RGB")
    s = min(560 / c.width, 300 / c.height)
    return c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)


def show():
    r = todo[state["i"]]
    try:
        a = ImageTk.PhotoImage(frame_img(r))
        img_lbl.config(image=a, text="")
        img_lbl.image = a
    except Exception as e:
        img_lbl.config(image="", text="frame not found: " + str(e))
    try:
        b = ImageTk.PhotoImage(crop_img(r))
        crop_lbl.config(image=b, text="")
        crop_lbl.image = b
    except Exception as e:
        crop_lbl.config(image="", text="crop not found: " + str(e))
    info.config(text=f"chunk {r['chunk'][-6:]}  track {r['track_id']}  {r['vehicle_label']}\n"
                     f"MODEL READ: {r['plate_text']}  [{r['format_status']}]")
    ent.delete(0, tk.END)
    vv.set("yes")
    pv.set("full")
    prog.config(text=f"{state['i'] + 1} / {len(todo)}")
    ent.focus_set()


def save(event=None):
    r = todo[state["i"]]
    row = {"chunk": r["chunk"], "track_id": r["track_id"], "vehicle_label": r["vehicle_label"],
           "model_plate": r["plate_text"], "format_status": r["format_status"],
           "human_plate": ent.get().strip().upper().replace(" ", ""),
           "vehicle_ok": vv.get(), "plate_visible": pv.get(),
           "best_crop_path": r["best_crop_path"], "best_image_path": r["best_image_path"]}
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    state["i"] += 1
    if state["i"] >= len(todo):
        print("All done. File:", OUT)
        root.destroy()
    else:
        show()


tk.Button(right, text="Save and next (Enter)", command=save, font=("Arial", 12)).pack(pady=6)
root.bind("<Return>", save)
show()
root.mainloop()