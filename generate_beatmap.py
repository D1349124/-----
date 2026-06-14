from pydub import AudioSegment
import os

AudioSegment.converter = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe")
AudioSegment.ffprobe   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffprobe.exe")

import json
import random
import numpy as np
import librosa

MUSIC_DIR    = "music"
MIN_INTERVAL = 0.6
START_OFFSET = 3.0   # 第一個 note 至少在音樂開始後幾秒才出現


def mp3_to_array(mp3_path: str):
    audio   = AudioSegment.from_mp3(mp3_path).set_channels(1)
    sr      = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples /= np.iinfo(audio.array_type).max
    return samples, sr


def generate(mp3_path: str, json_path: str):
    print(f"分析中：{os.path.basename(mp3_path)} ...")

    try:
        y, sr = mp3_to_array(mp3_path)
    except Exception as e:
        print(f"  ❌ 無法讀取，跳過：{e}")
        return

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times         = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # 全域過濾：所有 note 之間都至少間隔 MIN_INTERVAL 秒
    filtered_times = []
    last_time      = -999
    for t in beat_times:
        if t - last_time >= MIN_INTERVAL:
            filtered_times.append(t)
            last_time = t

    # 分配軌道：強迫不連續同軌道
    notes     = []
    prev_lane = -1
    for t in filtered_times:
        lanes = [0, 1, 2]
        if prev_lane in lanes:
            lanes.remove(prev_lane)
        lane      = random.choice(lanes)
        prev_lane = lane
        # ✅ 所有 note 往後推 START_OFFSET 秒
        notes.append({"time": round(t + START_OFFSET, 3), "lane": lane})

    data = {"bpm": round(float(tempo), 1), "notes": notes}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✅ 完成：{os.path.basename(json_path)}  ({len(notes)} notes, BPM={data['bpm']})")


def main():
    if not os.path.isdir(MUSIC_DIR):
        print(f'找不到 "{MUSIC_DIR}/" 資料夾')
        return

    mp3_files = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(".mp3")]

    if not mp3_files:
        print(f'"{MUSIC_DIR}/" 裡沒有 mp3 檔案')
        return

    for fname in mp3_files:
        mp3_path  = os.path.join(MUSIC_DIR, fname)
        json_path = os.path.join(MUSIC_DIR, os.path.splitext(fname)[0] + ".json")
        generate(mp3_path, json_path)

    print("\n全部完成，可以執行 main.py 了。")


if __name__ == "__main__":
    main()