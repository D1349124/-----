# fix_beatmap.py
import os
import json
import random

MUSIC_DIR  = "music"
MIN_INTERVAL = 1.2   # 秒，可以調整

def fix(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    notes = sorted(data["notes"], key=lambda n: n["time"])

    # 全域過濾，確保任意兩個 note 間距 >= MIN_INTERVAL
    filtered = []
    last_time = -999
    prev_lane = -1

    for n in notes:
        if n["time"] - last_time < MIN_INTERVAL:
            continue

        # 強迫換道
        lanes = [0, 1, 2]
        if prev_lane in lanes:
            lanes.remove(prev_lane)
        lane = random.choice(lanes)

        filtered.append({"time": n["time"], "lane": lane})
        last_time = n["time"]
        prev_lane = lane

    data["notes"] = filtered

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ {os.path.basename(json_path)}：{len(notes)} → {len(filtered)} notes")

def main():
    for fname in os.listdir(MUSIC_DIR):
        if fname.lower().endswith(".json"):
            fix(os.path.join(MUSIC_DIR, fname))

if __name__ == "__main__":
    main()