# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import json, os, subprocess, sys

D = sys.argv[1]
LA_DIR = _os.path.join(ROOT, 'models', 'LocateAnything-3B')
GROUP = 6
LIMIT = 45
env = dict(os.environ, PYTHONUTF8="1")
rows = [json.loads(l) for l in open(os.path.join(D, "crop_requests_small.jsonl"), encoding="utf-8") if l.strip()]
final = os.path.join(D, "crop_results.jsonl")
open(final, "w", encoding="utf-8").close()
fin = os.path.join(D, "group_in.jsonl")
fout = os.path.join(D, "group_out.jsonl")
skipped = 0
for g in range(0, len(rows), GROUP):
    part = rows[g:g + GROUP]
    n = g // GROUP + 1
    if os.path.exists(fout):
        os.remove(fout)
    with open(fin, "w", encoding="utf-8") as f:
        for r in part:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cmd = [sys.executable, "batch_infer.py", "--attn", "sdpa", "--vision-attn", "sdpa",
           "--max-new-tokens", "512", "--batch-size", "1", "--requests", fin, "--out", fout]
    try:
        p = subprocess.run(cmd, cwd=LA_DIR, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=LIMIT)
        ok = p.returncode == 0 and os.path.exists(fout)
    except subprocess.TimeoutExpired:
        ok = False
    if ok:
        with open(final, "a", encoding="utf-8") as out:
            out.write(open(fout, encoding="utf-8").read())
        print(f"group {n} done ({len(part)} crops)", flush=True)
    else:
        skipped += len(part)
        print(f"group {n} SKIPPED ({len(part)} crops)", flush=True)
print("crops searched:", len(rows) - skipped, "| skipped:", skipped)
if rows and skipped > len(rows) // 2:
    sys.exit(1)