import csv, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
LA_DIR = os.path.join(ROOT, "models", "LocateAnything-3B")
SCRIPT_DIRS = [os.path.join(ROOT, "scripts"), ROOT]
ENV_PY = os.path.join(ROOT, "plate_env", "Scripts", "python.exe")
PY = ENV_PY if os.path.exists(ENV_PY) else sys.executable
FFMPEG = "ffmpeg"
READER = "read_plates_d.py"
FPS = 5
STATUS = os.path.join(ROOT, "chunk_status.csv")
WORK = os.path.join(ROOT, "work")
FIELDS = ["chunk", "status", "stage", "frames", "reason", "updated"]
TIMEOUT = {"locate_frames": 1500, "locate_crops": 600, "read_plates": 300}


def set_status(chunk, status, stage="", frames="", reason=""):
    rows = {}
    if os.path.exists(STATUS):
        for r in csv.DictReader(open(STATUS, encoding="utf-8-sig")):
            rows[r["chunk"]] = r
    old = rows.get(chunk, {})
    rows[chunk] = {"chunk": chunk, "status": status, "stage": stage,
                   "frames": frames if frames != "" else old.get("frames", ""),
                   "reason": reason, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(STATUS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows.values())


def script(name):
    for d in SCRIPT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def has_pairs(path):
    try:
        return any(r.get("status") == "ok" for r in csv.DictReader(open(path, encoding="utf-8-sig")))
    except Exception:
        return True


def run(chunk, stage, cmd, cwd, logdir):
    set_status(chunk, "running", stage)
    print(f"[{time.strftime('%H:%M:%S')}] {stage} ...", flush=True)
    t = time.time()
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT.get(stage))
    except subprocess.TimeoutExpired:
        set_status(chunk, "failed", stage, reason=f"timeout after {TIMEOUT.get(stage)}s")
        print(f"   FAILED at {stage}: timeout after {TIMEOUT.get(stage)}s", flush=True)
        return False
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, stage + ".log"), "w", encoding="utf-8") as f:
        f.write((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""))
    sec = round(time.time() - t)
    if r.returncode != 0:
        msg = ((r.stderr or r.stdout or "")[-200:]).replace("\n", " ")
        set_status(chunk, "failed", stage, reason=msg)
        print(f"   FAILED at {stage} after {sec}s. See logs\\{stage}.log", flush=True)
        return False
    print(f"   ok ({sec}s)", flush=True)
    return True


def step1_frames(video, chunk, frames_dir, logdir):
    os.makedirs(frames_dir, exist_ok=True)
    for old in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, old))
    if not os.path.exists(video) or os.path.getsize(video) < 1_000_000:
        set_status(chunk, "failed", "frames", reason="video missing or too small")
        print("   FAILED: video missing or too small")
        return False
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", video, "-vf", f"fps={FPS}",
           "-q:v", "2", os.path.join(frames_dir, chunk + "_f_%03d.jpg")]
    if not run(chunk, "frames", cmd, ROOT, logdir):
        return False
    n = len([x for x in os.listdir(frames_dir) if x.endswith(".jpg")])
    if n == 0:
        set_status(chunk, "failed", "frames", reason="ffmpeg gave no frames")
        return False
    set_status(chunk, "running", "frames_done", frames=n)
    print(f"   frames: {n}")
    return True


def process(video):
    t0 = time.time()
    chunk = os.path.splitext(os.path.basename(video))[0]
    W = os.path.join(WORK, chunk)
    P = lambda n: os.path.join(W, n)
    logs = P("logs")
    frames, vcrops, best = P("frames"), P("vcrops"), P("best")
    shutil.rmtree(vcrops, ignore_errors=True)
    shutil.rmtree(best, ignore_errors=True)
    set_status(chunk, "running", "start")
    if not step1_frames(video, chunk, frames, logs):
        return
    py = PY
    la = [py, "batch_infer.py", "--attn", "sdpa", "--vision-attn", "sdpa", "--max-new-tokens", "8192"]
    stages = [
        ("requests", [py, script("make_requests_dir.py"), frames, P("requests.jsonl")], ROOT),
        ("locate_frames", la + ["--requests", P("requests.jsonl"), "--out", P("results.jsonl")], LA_DIR),
        ("detections", [py, script("make_csv_pilot.py"), P("results.jsonl"), P("detections.csv")], ROOT),
        ("lane_filter", [py, script("apply_roi.py"), P("detections.csv"), os.path.join(ROOT, "roi.json"), P("roi.csv")], ROOT),
        ("pairs", [py, script("final_select.py"), P("roi.csv"), P("pairs.csv")], ROOT),
        ("crop_prep", [py, script("second_pass_prep.py"), frames, P("roi.csv"), P("pairs.csv"), vcrops], ROOT),
        ("shrink_crops", [py, script("shrink_crops.py"), vcrops], ROOT),
        ("locate_crops", [py, script("locate_crops_grouped.py"), vcrops], ROOT),
        ("crop_merge", [py, script("second_pass_merge.py"), os.path.join(vcrops, "crop_map.csv"), os.path.join(vcrops, "crop_results.jsonl"), P("pairs.csv"), P("final.csv")], ROOT),
        ("tracking", [py, script("track_best.py"), frames, P("final.csv"), P("vehicles.csv"), best], ROOT),
        ("read_plates", [py, script(READER), best, P("plates.csv")], ROOT),
        ("fix_state", [py, script("fix_state.py"), P("plates.csv"), P("plates_fixed.csv")], ROOT),
        ("validate", [py, script("validate_plates.py"), P("plates_fixed.csv"), P("plates_checked.csv")], ROOT),
        ("join", [py, script("join_results.py"), P("vehicles.csv"), P("plates_checked.csv"), P("result.csv"), chunk, str(FPS), frames, best], ROOT),
    ]
    for stage, cmd, cwd in stages:
        if not run(chunk, stage, cmd, cwd, logs):
            return
        if stage == "crop_merge" and not has_pairs(P("final.csv")):
            set_status(chunk, "done", "no_vehicles")
            print("DONE: no vehicle with a plate in this chunk")
            return
    set_status(chunk, "done", "finished")
    mins = round((time.time() - t0) / 60, 1)
    print(f"DONE in {mins} min -> {P('result.csv')}")


if __name__ == "__main__":
    process(sys.argv[1])