import random
from config import *


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
        self.reset()

    def reset(self):
        self.tiles:         list[Tile]        = []
        self.judge_results: list[JudgeResult] = []
        self.score         = 0
        self.combo         = 0
        self.max_combo     = 0
        self.frame_count   = 0
        self.current_speed = TILE_SPEED_INITIAL
        self.game_over     = False
        self.miss_count    = 0
        self.MAX_MISS      = 10
        self._gesture_cooldown = {i: 0 for i in range(LANE_COUNT)}
        self.GESTURE_COOLDOWN_FRAMES = 8

    # ---------- 每幀更新 ----------

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

    # ---------- 生成方格 ----------

    def _spawn_tile(self):
        if self.frame_count % SPAWN_INTERVAL == 0:
            lane = random.randint(0, LANE_COUNT - 1)
            self.tiles.append(Tile(lane, self.current_speed))

    # ---------- 更新方格位置 ----------

    def _update_tiles(self):
        for tile in self.tiles:
            tile.update()

    # ---------- 清除離開畫面的方格 ----------

    def _cleanup_tiles(self):
        self.tiles = [t for t in self.tiles if not t.is_off_screen()]

    # ---------- Miss 判定（方格離開畫面才觸發） ----------

    def _check_miss(self):
        for tile in self.tiles:
            if tile.judged:
                continue
            if tile.is_off_screen():
                tile.judged = True
                self._register_miss(tile.lane)

    # ---------- 手勢判定 ----------

    def _process_gesture(self, gesture: str | None):
        if gesture is None:
            return

        lane = GESTURE_TO_LANE.get(gesture)
        if lane is None:
            return

        if self._gesture_cooldown[lane] > 0:
            return

        candidates = [
            t for t in self.tiles
            if t.lane == lane and not t.judged
        ]
        if not candidates:
            return

        closest = max(candidates, key=lambda t: t.y)

        # 方格還太遠時忽略，避免太早誤觸
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

    # ---------- 冷卻更新 ----------

    def _update_cooldowns(self):
        for lane in self._gesture_cooldown:
            if self._gesture_cooldown[lane] > 0:
                self._gesture_cooldown[lane] -= 1

    # ---------- 判定結果 ----------

    def _register_perfect(self, lane: int):
        self.combo     += 1
        self.max_combo  = max(self.combo, self.max_combo)
        self.score     += 100 + self.combo * 2
        self._speed_up()
        self.judge_results.append(JudgeResult("PERFECT!", lane, COLOR_PERFECT))

    def _register_good(self, lane: int):
        self.combo     += 1
        self.max_combo  = max(self.combo, self.max_combo)
        self.score     += 50
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
                TILE_SPEED_INITIAL + (self.combo // 10) * TILE_SPEED_INCREMENT,
                12.0
            )
            for tile in self.tiles:
                tile.speed = self.current_speed

    def _update_judge_results(self):
        for jr in self.judge_results:
            jr.alpha    -= 5
            jr.y_offset -= 1
        self.judge_results = [jr for jr in self.judge_results if jr.alpha > 0]