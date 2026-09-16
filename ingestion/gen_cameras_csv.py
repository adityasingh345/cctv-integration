#!/usr/bin/env python3
"""
Generate a registry CSV of N cameras scattered around a city centre, with
rtsp_url = rtsp://mediamtx:8554/camNNN so they line up with simulate_cameras.py.

Example:
    python ingestion/gen_cameras_csv.py --count 50 --out data/cameras_50.csv
Then bulk-upload data/cameras_50.csv via POST /cameras/bulk-upload.
"""
import csv, random, argparse

DEPTS = ["Traffic", "Police", "Municipal", "Transport"]
TYPES = ["fixed", "ptz", "anpr"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--lat", type=float, default=26.4499, help="centre latitude (Kanpur)")
    ap.add_argument("--lng", type=float, default=80.3319, help="centre longitude (Kanpur)")
    ap.add_argument("--spread", type=float, default=0.05, help="coordinate jitter in degrees")
    ap.add_argument("--out", default="data/cameras_50.csv")
    args = ap.parse_args()

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["camera_code", "name", "department", "camera_type",
                    "rtsp_url", "latitude", "longitude", "status"])
        for i in range(1, args.count + 1):
            lat = round(args.lat + random.uniform(-args.spread, args.spread), 6)
            lng = round(args.lng + random.uniform(-args.spread, args.spread), 6)
            w.writerow([
                f"KNP-CAM-{i:03d}",
                f"Camera {i:03d}",
                random.choice(DEPTS),
                random.choice(TYPES),
                f"rtsp://mediamtx:8554/cam{i:03d}",
                lat, lng, "online",
            ])
    print(f"Wrote {args.count} cameras -> {args.out}")

if __name__ == "__main__":
    main() 