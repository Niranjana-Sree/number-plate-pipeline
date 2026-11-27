# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import json, os, subprocess, sys, time

D = sys.argv[1]
LA_DIR = _os.path.join(ROOT, 'models', 'LocateAnything-3B')
LIMIT = 90
env = dict(os.environ, PYTHONUTF8="1")
rows = [json.loads(l) for l in open(os.path.join(D, "crop_requests_small.jsonl"), encoding="utf-8") if l.strip()]
tmp_in = os.path.join(D, "probe_one.jsonl")
tmp_out = os.path.join(D, "probe_one_out.jsonl")
for i, r in enumerate(rows, 1):
    with open(tmp_in, "w", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cmd = [sys.executable, "batch_infer.py", "--attn", "sdpa", "--vision-attn", "sdpa",
           "--max-new-tokens", "512", "--requests", tmp_in, "--out", tmp_out]
    t = time.time()
    name = os.path.basename(r["image"])
    try:
        p = subprocess.run(cmd, cwd=LA_DIR, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=LIMIT)
        status = "ok" if p.returncode == 0 else "ERROR"
    except subprocess.TimeoutExpired:
        print(f"{i}/{len(rows)} {name}: HANG (>{LIMIT}s). Stopping here.", flush=True)
        break
    print(f"{i}/{len(rows)} {name}: {status} {round(time.time() - t)}s", flush=True)