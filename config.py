# ===== 畫面設定 =====
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# ===== 軌道設定 =====
LANE_COUNT = 3
LANE_LABELS = ["Thumbs Up", "Open Palm", "Scissors"]
LANE_COLORS = [
    (100, 200, 255),
    (100, 255, 150),
    (200, 150, 255),
]
LANE_WIDTH = 180
LANE_GAP = 60

# ===== 方格設定 =====
TILE_HEIGHT = 80
TILE_SPEED_INITIAL = 4
TILE_SPEED_INCREMENT = 0.3
SPAWN_INTERVAL = 90

# ===== 判定線 =====
JUDGE_LINE_Y = 580
JUDGE_PERFECT_RANGE = 40
JUDGE_GOOD_RANGE = 80

# ===== 手勢對應軌道 =====
GESTURE_TO_LANE = {
    "thumbs_up": 0,
    "open_palm":  1,
    "scissors":   2,
}

# ===== 顏色 =====
COLOR_BG         = (15,  15,  30)
COLOR_JUDGE_LINE = (255, 255, 100)
COLOR_PERFECT    = (255, 230, 50)
COLOR_GOOD       = (100, 255, 180)
COLOR_MISS       = (255, 80,  80)
COLOR_TEXT       = (240, 240, 240)
COLOR_DIM        = (120, 120, 140)
COLOR_BTN        = (60,  60,  120)
COLOR_BTN_HOVER  = (90,  90,  180)
COLOR_BTN_BORDER = (150, 150, 255)

# ===== 倒數秒數 =====
COUNTDOWN_SECONDS = 3

# ===== 音樂目錄 =====
MUSIC_DIR = "music"

# ===== 難度設定 =====
DIFFICULTIES = {
    "Easy":   {"speed": 3.0, "max_miss": 15, "spawn_interval": 120},
    "Normal": {"speed": 4.0, "max_miss": 10, "spawn_interval": 90},
    "Hard":   {"speed": 6.0, "max_miss": 5,  "spawn_interval": 70},
}