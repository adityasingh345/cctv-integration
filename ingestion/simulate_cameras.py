#!/usr/bin/env python3
"""
Simulate N CCTV cameras by re-streaming local video file(s) as RTSP feeds
into MediaMTX. Each camera becomes rtsp://<host>:8554/camNNN, which MediaMTX
also exposes as HLS at http://<host>:8888/camNNN/index.m3u8.

Run this ON THE HOST (not in Docker) after `docker compose up mediamtx`.

Examples
--------
# 5 cameras from every video in ./clips (source must be H.264 for --copy)
python ingestion/simulate_cameras.py --videos ./clips --count 5

# 50 cameras, re-encode arbitrary videos to H.264 on the fly (heavy on CPU!)
python ingestion/simulate_cameras.py --videos ./clips --count 50 --reencode
"""
import os, sys, glob, time, argparse, subprocess, signal

def find_videos(path):
    if os.path.isfile(path):
        return [path]
    vids = []
    for ext in ("*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm"):
        vids += glob.glob(os.path.join(path, ext))
    return sorted(vids)

def ffmpeg_cmd(video, rtsp_url, reencode):
    base = ["ffmpeg", "-loglevel", "error", "-re", "-stream_loop", "-1", "-i", video]
    if reencode:
        vcodec = ["-c:v", "libx264", "-preset", "veryfast",
                  "-tune", "zerolatency", "-pix_fmt", "yuv420p", "-g", "30"]
    else:
        vcodec = ["-c:v", "copy"]          # cheap: assumes source is already H.264
    return base + vcodec + ["-an", "-f", "rtsp", "-rtsp_transport", "tcp", rtsp_url]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", required=True, help="video file or folder of clips")
    ap.add_argument("--count", type=int, default=5, help="how many camera streams")
    ap.add_argument("--host", default="localhost", help="MediaMTX host")
    ap.add_argument("--port", type=int, default=8554, help="MediaMTX RTSP port")
    ap.add_argument("--reencode", action="store_true",
                    help="re-encode to H.264 (use for non-H.264 sources; CPU heavy)")
    args = ap.parse_args()

    videos = find_videos(args.videos)
    if not videos:
        sys.exit(f"No videos found in {args.videos}")
    print(f"Found {len(videos)} source video(s); starting {args.count} camera streams...")

    procs = []
    for i in range(1, args.count + 1):
        video = videos[(i - 1) % len(videos)]          # cycle through clips
        url = f"rtsp://{args.host}:{args.port}/cam{i:03d}"
        procs.append(subprocess.Popen(ffmpeg_cmd(video, url, args.reencode)))
        print(f"  cam{i:03d}  <-  {os.path.basename(video)}  ->  {url}")
        time.sleep(0.3)                                # stagger startups

    print(f"\n{len(procs)} streams live. HLS: http://{args.host}:8888/cam001/index.m3u8")
    print("Press Ctrl+C to stop all.\n")

    def stop(*_):
        print("\nStopping all streams...")
        for p in procs:
            p.terminate()
        for p in procs:
            try: p.wait(timeout=5)
            except Exception: p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()