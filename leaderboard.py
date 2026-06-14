"""
leaderboard.py
本地排行榜，用 JSON 儲存每首歌的紀錄。
"""
import json
import os

LEADERBOARD_FILE = "leaderboard.json"


def load_leaderboard() -> dict:
    if not os.path.isfile(LEADERBOARD_FILE):
        return {}
    with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_record(song: str, difficulty: str, score: int,
                max_combo: int, perfect: int, good: int, miss: int):
    """儲存一筆紀錄，只保留該歌曲+難度的最高分。"""
    data = load_leaderboard()
    key  = f"{song}|{difficulty}"

    existing = data.get(key, {})
    if score >= existing.get("score", 0):
        data[key] = {
            "song":       song,
            "difficulty": difficulty,
            "score":      score,
            "max_combo":  max_combo,
            "perfect":    perfect,
            "good":       good,
            "miss":       miss,
        }

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_record(song: str, difficulty: str) -> dict | None:
    data = load_leaderboard()
    return data.get(f"{song}|{difficulty}")


def get_rank(score: int, perfect: int, good: int, miss: int) -> str:
    """根據分數與準確率回傳等級"""
    total = perfect + good + miss
    if total == 0:
        return "D"
    accuracy = (perfect * 100 + good * 50) / (total * 100)

    if accuracy >= 0.95 and miss == 0:
        return "S"
    elif accuracy >= 0.90:
        return "A"
    elif accuracy >= 0.75:
        return "B"
    elif accuracy >= 0.55:
        return "C"
    else:
        return "D"