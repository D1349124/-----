import pygame
import sys
import time
import os
from enum import Enum, auto

from game_engine import GameEngine
from gesture_input import GestureInput
from renderer import Renderer
from beatmap import load_beatmap
from leaderboard import save_record, get_record, get_rank
from analyze_thread import BeatmapAnalyzer, open_file_dialog
from config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT, COUNTDOWN_SECONDS, MUSIC_DIR, DIFFICULTIES


class GameState(Enum):
    MENU        = auto()
    SETTINGS    = auto()
    SONG_SELECT = auto()
    IMPORTING   = auto()   # ✅ 新增：分析中畫面
    DIFFICULTY  = auto()
    COUNTDOWN   = auto()
    PLAYING     = auto()
    PAUSED      = auto()
    GAME_OVER   = auto()


def load_song_list() -> list[str]:
    if not os.path.isdir(MUSIC_DIR):
        os.makedirs(MUSIC_DIR)
        return []
    return sorted([
        f for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith(".mp3")
    ])


def get_song_length(filepath: str) -> float:
    try:
        sound = pygame.mixer.Sound(filepath)
        return sound.get_length()
    except Exception:
        return 0.0


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gesture Rhythm Game")
    clock = pygame.time.Clock()

    engine        = GameEngine()
    gesture_input = GestureInput()
    renderer      = Renderer(screen)

    gesture_input.start()

    state           = GameState.MENU
    prev_state      = GameState.MENU
    countdown_start = 0.0
    song_list       = load_song_list()
    selected_song   = None
    selected_diff   = "Easy"
    scroll_offset   = 0
    volume          = 0.8
    pygame.mixer.music.set_volume(volume)

    song_length = 0.0
    analyzer    = None   # ✅ 目前執行中的分析器

    last_rank   = "D"
    last_record = None

    running = True
    while running:

        mouse_pos   = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == GameState.PLAYING:
                        pygame.mixer.music.pause()
                        state = GameState.PAUSED
                    elif state == GameState.PAUSED:
                        pygame.mixer.music.unpause()
                        state = GameState.PLAYING
                    elif state == GameState.SETTINGS:
                        state = prev_state
                    elif state not in (GameState.PLAYING, GameState.PAUSED,
                                       GameState.SETTINGS, GameState.IMPORTING):
                        running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.MOUSEWHEEL:
                if state == GameState.SONG_SELECT:
                    scroll_offset = max(0, scroll_offset - event.y)

        # ── 狀態更新與渲染 ──────────────────────────────

        if state == GameState.MENU:
            result = renderer.draw_menu(mouse_pos, mouse_click)
            if result == "start":
                song_list     = load_song_list()
                scroll_offset = 0
                state         = GameState.SONG_SELECT
            elif result == "settings":
                prev_state = GameState.MENU
                state      = GameState.SETTINGS

        elif state == GameState.SETTINGS:
            new_volume = renderer.draw_settings(volume, mouse_pos, mouse_click)
            if new_volume == "back":
                state = prev_state
            elif new_volume is not None:
                volume = new_volume
                pygame.mixer.music.set_volume(volume)

        elif state == GameState.SONG_SELECT:
            result = renderer.draw_song_select(
                song_list, selected_song, scroll_offset, mouse_pos, mouse_click
            )
            if result == "back":
                state = GameState.MENU
            elif result == "import":
                # ✅ 開啟系統檔案選擇視窗
                path = open_file_dialog()
                if path:
                    analyzer = BeatmapAnalyzer(path)
                    analyzer.start()
                    state = GameState.IMPORTING
            elif result is not None:
                selected_song = result
                notes = load_beatmap(selected_song)
                engine.set_beatmap(notes)
                engine.reset()
                if notes:
                    extra_buffer = 200 / 3.0 / 60 + 2.0
                    song_length = notes[-1]["time"] + extra_buffer
                else:
                    song_length = get_song_length(os.path.join(MUSIC_DIR, selected_song))
                state = GameState.DIFFICULTY

        elif state == GameState.IMPORTING:
            renderer.draw_importing()
            if analyzer and analyzer.is_done():
                if analyzer.is_error():
                    # 分析失敗，顯示錯誤後返回選歌
                    print(f"[Import Error] {analyzer.is_error()}")
                    analyzer = None
                    song_list = load_song_list()
                    state = GameState.SONG_SELECT
                else:
                    # ✅ 分析成功，自動選中這首新歌
                    new_song      = analyzer.result_filename()
                    selected_song = new_song
                    song_list     = load_song_list()
                    notes         = load_beatmap(new_song)
                    engine.set_beatmap(notes)
                    engine.reset()
                    if notes:
                        extra_buffer = 200 / 3.0 / 60 + 2.0
                        song_length = notes[-1]["time"] + extra_buffer
                    analyzer = None
                    state = GameState.DIFFICULTY

        elif state == GameState.DIFFICULTY:
            result = renderer.draw_difficulty(selected_diff, mouse_pos, mouse_click)
            if result == "back":
                state = GameState.SONG_SELECT
            elif result is not None:
                selected_diff = result
                diff = DIFFICULTIES[selected_diff]
                engine.apply_difficulty(diff)
                engine.reset()
                engine.reset_beatmap_index()
                state           = GameState.COUNTDOWN
                countdown_start = time.time()

        elif state == GameState.COUNTDOWN:
            elapsed   = time.time() - countdown_start
            remaining = COUNTDOWN_SECONDS - int(elapsed)
            if remaining <= 0:
                pygame.mixer.music.load(os.path.join(MUSIC_DIR, selected_song))
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(0)
                engine.reset_beatmap_index()
                state = GameState.PLAYING
            else:
                renderer.draw_countdown(remaining)

        elif state == GameState.PLAYING:
            gesture = gesture_input.consume_gesture()
            engine.update(gesture)

            current_pos = pygame.mixer.music.get_pos() / 1000.0
            progress = 0.0
            if song_length > 0 and current_pos > 0:
                progress = min(1.0, current_pos / song_length)
            elif engine.check_song_finished():
                progress = 1.0

            renderer.draw(engine, progress)

            if engine.game_over or engine.check_song_finished():
                pygame.mixer.music.stop()
                save_record(
                    selected_song, selected_diff,
                    engine.score, engine.max_combo,
                    engine.perfect_count, engine.good_count, engine.miss_count
                )
                last_rank   = get_rank(engine.score, engine.perfect_count,
                                       engine.good_count, engine.miss_count)
                last_record = get_record(selected_song, selected_diff)
                state = GameState.GAME_OVER

        elif state == GameState.PAUSED:
            result = renderer.draw_pause(mouse_pos, mouse_click)
            if result == "continue":
                pygame.mixer.music.unpause()
                state = GameState.PLAYING
            elif result == "restart":
                pygame.mixer.music.stop()
                diff = DIFFICULTIES[selected_diff]
                engine.apply_difficulty(diff)
                engine.reset()
                engine.reset_beatmap_index()
                state           = GameState.COUNTDOWN
                countdown_start = time.time()
            elif result == "settings":
                prev_state = GameState.PAUSED
                state      = GameState.SETTINGS
            elif result == "home":
                pygame.mixer.music.stop()
                engine.reset()
                song_list     = load_song_list()
                scroll_offset = 0
                state         = GameState.MENU

        elif state == GameState.GAME_OVER:
            result = renderer.draw_game_over(
                engine, last_rank, last_record, mouse_pos, mouse_click
            )
            if result == "restart":
                diff = DIFFICULTIES[selected_diff]
                engine.apply_difficulty(diff)
                engine.reset()
                engine.reset_beatmap_index()
                state           = GameState.COUNTDOWN
                countdown_start = time.time()
            elif result == "menu":
                engine.reset()
                pygame.mixer.music.stop()
                song_list     = load_song_list()
                scroll_offset = 0
                state         = GameState.MENU

        clock.tick(FPS)

    gesture_input.stop()
    pygame.mixer.music.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()