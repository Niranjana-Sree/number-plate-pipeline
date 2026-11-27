import glob, json, os, sys
folder, out = sys.argv[1], sys.argv[2]
q = "car</c>truck</c>bus</c>motorcycle</c>bicycle</c>vehicle registration plate"
files = sorted(glob.glob(os.path.join(folder, "*.jpg")))
with open(out, "w", encoding="utf-8") as f:
    for p in files:
        f.write(json.dumps({"image": os.path.abspath(p), "query": q}) + "\n")
print("requests written:", len(files), "->", out)