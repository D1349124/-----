import json
import os
from config import MUSIC_DIR, JUDGE_LINE_Y, TILE_HEIGHT, TILE_SPEED_INITIAL


def load_beatmap(song_filename: str) -> list[dict] | None:
    base      = os.path.splitext(song_filename)[0]
    json_path = os.path.join(MUSIC_DIR, base + ".json")
    print(f"[beatmap] 嘗試載入：{json_path}")

    if not os.path.isfile(json_path):
        print(f"[beatmap] 找不到譜面，使用隨機模式")
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    notes = data.get("notes", [])

    valid = []
    for n in notes:
        if "time" in n and "lane" in n:
            if isinstance(n["time"], (int, float)) and n["lane"] in (0, 1, 2):
                valid.append({"time": float(n["time"]), "lane": int(n["lane"])})

    print(f"[beatmap] 載入成功：{len(valid)} notes")
    return sorted(valid, key=lambda n: n["time"])


def calculate_spawn_offset(speed: float) -> float:
    distance = JUDGE_LINE_Y + TILE_HEIGHT
    frames   = distance / speed
    return frames / 60.0


class BeatmapPlayer:
    def __init__(self, notes: list[dict], speed: float = TILE_SPEED_INITIAL):
        self._offset = calculate_spawn_offset(speed)
        self._notes  = [
            {"trigger": max(0.0, n["time"] - self._offset), "lane": n["lane"]}
            for n in notes
        ]
        self._index = 0

    def reset(self):
        self._index = 0

    def update(self, music_time: float) -> list[int]:
        lanes = []
        while (self._index < len(self._notes) and
               self._notes[self._index]["trigger"] <= music_time):
            lanes.append(self._notes[self._index]["lane"])
            self._index += 1
        return lanes