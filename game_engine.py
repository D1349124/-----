import random
import pygame
from config import *
from beatmap import BeatmapPlayer


class Tile:
    def __init__(self, lane: int, speed: float):
        self.lane   = lane
        self.y      = -TILE_HEIGHT
        self.speed  = speed
        self.judged = False

    def update(self):
        self.y += self.speed

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_HEIGHT


class JudgeResult:
    def __init__(self, text: str, lane: int, color: tuple):
        self.text     = text
        self.lane     = lane
        self.color    = color
        self.alpha    = 255
        self.y_offset = 0


class GameEngine:
    def __init__(self):
        self._beatmap_player: BeatmapPlayer | None = None
        self.MAX_MISS       = 10
        self.SPAWN_INTERVAL = SPAWN_INTERVAL
        self.current_speed  = TILE_SPEED_INITIAL
        self.reset()

    def set_beatmap(self, notes: list[dict] | None):
        if notes is not None:
            self._beatmap_player = BeatmapPlayer(notes, self.current_speed)
        else:
            self._beatmap_player = None

    def apply_difficulty(self, diff: dict):
        self.current_speed  = diff["speed"]
        self.MAX_MISS       = diff["max_miss"]
        self.SPAWN_INTERVAL = diff.get("spawn_interval", SPAWN_INTERVAL)

    def reset(self):
        self.tiles:         list[Tile]        = []
        self.judge_results: list[JudgeResult] = []
        self.score         = 0
        self.combo         = 0
        self.max_combo     = 0
        self.frame_count   = 0
        self.game_over     = False
        self.miss_count    = 0
        self.perfect_count = 0   # ✅ 新增
        self.good_count    = 0   # ✅ 新增
        self._finish_timer       = 0
        self.FINISH_DELAY_FRAMES = 90 
        self._gesture_cooldown       = {i: 0 for i in range(LANE_COUNT)}
        self.GESTURE_COOLDOWN_FRAMES = 8

        if self._beatmap_player:
            self._beatmap_player.reset()

    def reset_beatmap_index(self):
        if self._beatmap_player:
            self._beatmap_player.reset()

    def update(self, gesture: str | None):
        if self.game_over:
            return
        self.frame_count += 1
        self._spawn_tile()
        self._update_tiles()
        self._process_gesture(gesture)
        self._check_miss()
        self._cleanup_tiles()
        self._update_judge_results()
        self._update_cooldowns()

    def _spawn_tile(self):
        if self._beatmap_player:
            music_time = pygame.mixer.music.get_pos() / 1000.0
            if music_time < 0:
                return
            for lane in self._beatmap_player.update(music_time):
                self.tiles.append(Tile(lane, self.current_speed))
        else:
            if self.frame_count % self.SPAWN_INTERVAL == 0:
                lane = random.randint(0, LANE_COUNT - 1)
                self.tiles.append(Tile(lane, self.current_speed))

    def _update_tiles(self):
        for tile in self.tiles:
            tile.update()

    def _cleanup_tiles(self):
        self.tiles = [t for t in self.tiles if not t.is_off_screen()]

    def _check_miss(self):
        for tile in self.tiles:
            if tile.judged:
                continue
            if tile.is_off_screen():
                tile.judged = True
                self._register_miss(tile.lane)

    def _process_gesture(self, gesture: str | None):
        if gesture is None:
            return
        lane = GESTURE_TO_LANE.get(gesture)
        if lane is None:
            return
        if self._gesture_cooldown[lane] > 0:
            return

        candidates = [t for t in self.tiles if t.lane == lane and not t.judged]
        if not candidates:
            return

        closest = max(candidates, key=lambda t: t.y)
        if closest.y < JUDGE_LINE_Y - JUDGE_GOOD_RANGE - TILE_HEIGHT:
            return

        distance = abs(closest.y - JUDGE_LINE_Y)
        closest.judged = True
        self._gesture_cooldown[lane] = self.GESTURE_COOLDOWN_FRAMES

        if distance <= JUDGE_PERFECT_RANGE:
            self._register_perfect(lane)
        elif distance <= JUDGE_GOOD_RANGE:
            self._register_good(lane)
        else:
            self._register_miss(lane)

    def _update_cooldowns(self):
        for lane in self._gesture_cooldown:
            if self._gesture_cooldown[lane] > 0:
                self._gesture_cooldown[lane] -= 1

    def _register_perfect(self, lane: int):
        self.combo         += 1
        self.max_combo      = max(self.combo, self.max_combo)
        self.score         += 100 + self.combo * 2
        self.perfect_count += 1   # ✅
        self._speed_up()
        self.judge_results.append(JudgeResult("PERFECT!", lane, COLOR_PERFECT))

    def _register_good(self, lane: int):
        self.combo      += 1
        self.max_combo   = max(self.combo, self.max_combo)
        self.score      += 50
        self.good_count += 1   # ✅
        self.judge_results.append(JudgeResult("GOOD", lane, COLOR_GOOD))

    def _register_miss(self, lane: int):
        self.combo       = 0
        self.miss_count += 1
        self.judge_results.append(JudgeResult("MISS", lane, COLOR_MISS))
        if self.miss_count >= self.MAX_MISS:
            self.game_over = True

    def _speed_up(self):
        if self.combo % 10 == 0:
            self.current_speed = min(
                self.current_speed + TILE_SPEED_INCREMENT, 12.0
            )
            for tile in self.tiles:
                tile.speed = self.current_speed

    def _update_judge_results(self):
        for jr in self.judge_results:
            jr.alpha    -= 5
            jr.y_offset -= 1
        self.judge_results = [jr for jr in self.judge_results if jr.alpha > 0]

    def check_song_finished(self) -> bool:
        """所有方格清空後，緩 1~2 秒才視為過關，避免結算太突然"""
        if not pygame.mixer.music.get_busy() and len(self.tiles) == 0 and self.frame_count > 60:
            self._finish_timer += 1
            if self._finish_timer >= self.FINISH_DELAY_FRAMES:
                return True
        else:
            self._finish_timer = 0   # 還有方格或音樂還在播，重置計時
        return False