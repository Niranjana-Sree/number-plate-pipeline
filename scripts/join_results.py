import csv, os, sys
VEH, CHK, OUT, CHUNK, FPS, IMG_DIR, BEST_DIR = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6], sys.argv[7]
chk = {r["crop_file"]: r for r in csv.DictReader(open(CHK, encoding="utf-8-sig"))}
fields = ["chunk", "track_id", "time_in_chunk_s", "best_time_s", "n_frames", "vehicle_label", "vx1", "vy1", "vx2", "vy2",
          "px1", "py1", "px2", "py2", "plate_text", "format_status", "reason", "best_image", "best_image_path", "best_crop", "best_crop_path"]
out = []
for v in csv.DictReader(open(VEH, encoding="utf-8-sig")):
    c = chk.get(v["best_crop"], {})
    ptxt = c.get("plate_clean", "")
    pstat = c.get("format_status", "not_read")
    preason = c.get("reason", "")
    if ptxt == "UNREADABLE":
        ptxt, pstat, preason = "", "unreadable", "model said the plate is not readable"
    digits = "".join(ch for ch in os.path.splitext(v["best_image"])[0].split("_")[-1] if ch.isdigit())
    best_t = round(float(digits) / FPS, 1) if digits else ""
    out.append({"chunk": CHUNK, "track_id": v["track_id"], "time_in_chunk_s": round(float(v["first_frame"]) / FPS, 1), "best_time_s": best_t,
                "n_frames": v["n_frames"], "vehicle_label": v["vehicle_label"],
                "vx1": round(float(v["vx1"])), "vy1": round(float(v["vy1"])), "vx2": round(float(v["vx2"])), "vy2": round(float(v["vy2"])),
                "px1": round(float(v["px1"])), "py1": round(float(v["py1"])), "px2": round(float(v["px2"])), "py2": round(float(v["py2"])),
                "plate_text": ptxt, "format_status": pstat, "reason": preason,
                "best_image": v["best_image"], "best_image_path": os.path.abspath(os.path.join(IMG_DIR, v["best_image"])),
                "best_crop": v["best_crop"], "best_crop_path": os.path.abspath(os.path.join(BEST_DIR, v["best_crop"]))})
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out)
print("vehicles:", len(out), "| with a plate reading:", sum(1 for r in out if r["plate_text"]), "| saved:", OUT)