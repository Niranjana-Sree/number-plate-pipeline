#!/usr/bin/env python3
"""
Save a live stream (RTSP / HTTP / HLS / webcam) as fixed-length video chunks.
Auto-reconnects if the stream drops. Needs ffmpeg on PATH.

Examples:
  python stream_chunker.py --url "rtsp://user:pass@192.168.1.50:554/stream1" --out chunks --chunk-sec 30
  python stream_chunker.py --url "http://192.168.1.50:8080/video" --out chunks --chunk-sec 60
  python stream_chunker.py --url ... --reencode      # exact chunk lengths (slower, uses CPU)
"""
import argparse, os, shutil, subprocess, sys, time


def build_cmd(a):
    pattern = os.path.join(a.out, f"{a.prefix}_%Y%m%d_%H%M%S.{a.ext}")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y"]
    if a.url.lower().startswith("rtsp"):
        if a.transport != "auto":
            cmd += ["-rtsp_transport", a.transport]
    cmd += ["-i", a.url, "-an"]  # -an: drop audio (not needed for vehicle models)
    if a.reencode:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-force_key_frames", f"expr:gte(t,n_forced*{a.chunk_sec})"]
    else:
        cmd += ["-c:v", "copy"]  # no re-encode: cuts land on keyframes, so lengths are approximate
    cmd += ["-f", "segment", "-segment_time", str(a.chunk_sec),
            "-reset_timestamps", "1", "-strftime", "1", pattern]
    return cmd


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True, help="stream URL (rtsp/http/hls) or webcam index/device")
    p.add_argument("--out", default="chunks", help="output folder")
    p.add_argument("--chunk-sec", type=int, default=30, help="seconds per chunk")
    p.add_argument("--prefix", default="cam")
    p.add_argument("--ext", default="mkv", help="mkv/ts survive crashes; mp4 can corrupt if killed")
    p.add_argument("--reencode", action="store_true")
    p.add_argument("--transport", default="udp", choices=["udp", "tcp", "auto"],
                   help="RTSP transport; try the other one if no chunks appear")
    p.add_argument("--retry-sec", type=int, default=5)
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install it first (Windows: winget install ffmpeg).")
    os.makedirs(a.out, exist_ok=True)

    while True:
        print(f"[{time.strftime('%H:%M:%S')}] capturing -> {a.out} ({a.chunk_sec}s chunks)")
        try:
            rc = subprocess.call(build_cmd(a))
        except KeyboardInterrupt:
            print("\nstopped."); break
        print(f"ffmpeg exited ({rc}); reconnecting in {a.retry_sec}s (Ctrl+C to quit)")
        try:
            time.sleep(a.retry_sec)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()