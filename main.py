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
from config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT, COUNTDOWN_SECONDS, MUSIC_DIR, DIFFICULTIES


class GameState(Enum):
    MENU        = auto()
    SETTINGS    = auto()
    SONG_SELECT = auto()
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

    # ✅ 結算用暫存
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
                        if prev_state == GameState.PAUSED:
                            pass
                    elif state not in (GameState.PLAYING, GameState.PAUSED,
                                       GameState.SETTINGS):
                        running = False

                if state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        diff = DIFFICULTIES[selected_diff]
                        engine.apply_difficulty(diff)
                        engine.reset()
                        engine.reset_beatmap_index()
                        state           = GameState.COUNTDOWN
                        countdown_start = time.time()
                    if event.key == pygame.K_m:
                        engine.reset()
                        pygame.mixer.music.stop()
                        song_list     = load_song_list()
                        scroll_offset = 0
                        state         = GameState.MENU

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
            elif result is not None:
                selected_song = result
                notes = load_beatmap(selected_song)
                engine.set_beatmap(notes)
                engine.reset()
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
            renderer.draw(engine)
            if engine.game_over:
                pygame.mixer.music.stop()
                # ✅ 儲存紀錄並計算等級
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
            # ✅ 傳入統計與等級
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