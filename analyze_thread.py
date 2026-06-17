import os
import json
import random
import threading
import shutil

from pydub import AudioSegment
import numpy as np
import librosa

from config import MUSIC_DIR

MIN_INTERVAL = 0.8
START_OFFSET = 3.0

_base = os.path.dirname(os.path.abspath(__file__))
AudioSegment.converter = os.path.join(_base, "ffmpeg.exe")
AudioSegment.ffprobe   = os.path.join(_base, "ffprobe.exe")


class BeatmapAnalyzer:
    """
    背景分析 mp3 並生成譜面。
    使用方式：
        analyzer = BeatmapAnalyzer(src_path)
        analyzer.start()
        # 每幀檢查 analyzer.is_done() / analyzer.is_error()
    """

    def __init__(self, src_path: str):
        self.src_path   = src_path
        self.filename    = os.path.basename(src_path)
        self._thread     = None
        self._done        = False
        self._error       = None
        self._result_name = None   # 成功後的檔名（複製到 music/ 後的名稱）

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def is_done(self) -> bool:
        return self._done

    def is_error(self) -> str | None:
        return self._error

    def result_filename(self) -> str | None:
        return self._result_name

    # ---------- 背景執行 ----------

    def _run(self):
        try:
            dest_path = os.path.join(MUSIC_DIR, self.filename)

            # 避免覆蓋同名檔案
            base, ext = os.path.splitext(self.filename)
            counter = 1
            while os.path.isfile(dest_path):
                dest_path = os.path.join(MUSIC_DIR, f"{base}_{counter}{ext}")
                counter += 1

            shutil.copy(self.src_path, dest_path)

            json_path = os.path.splitext(dest_path)[0] + ".json"
            self._generate(dest_path, json_path)

            self._result_name = os.path.basename(dest_path)
            self._done = True

        except Exception as e:
            self._error = str(e)
            self._done = True

    def _generate(self, mp3_path: str, json_path: str):
        y, sr = self._mp3_to_array(mp3_path)

        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        filtered_times = []
        last_time = -999
        for t in beat_times:
            if t - last_time >= MIN_INTERVAL:
                filtered_times.append(t)
                last_time = t

        notes = []
        prev_lane = -1
        for t in filtered_times:
            lanes = [0, 1, 2]
            if prev_lane in lanes:
                lanes.remove(prev_lane)
            lane = random.choice(lanes)
            prev_lane = lane
            notes.append({"time": round(t + START_OFFSET, 3), "lane": lane})

        data = {"bpm": round(float(tempo), 1), "notes": notes}

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _mp3_to_array(self, mp3_path: str):
        audio   = AudioSegment.from_mp3(mp3_path).set_channels(1)
        sr      = audio.frame_rate
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples /= np.iinfo(audio.array_type).max
        return samples, sr


def open_file_dialog() -> str | None:
    """
    呼叫系統檔案選擇視窗，回傳選中的 mp3 路徑，取消則回傳 None。
    使用 tkinter，僅在呼叫時才初始化，不影響 pygame。
    """
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = filedialog.askopenfilename(
        title="選擇 MP3 檔案",
        filetypes=[("MP3 files", "*.mp3")]
    )
    root.destroy()
    return path if path else None