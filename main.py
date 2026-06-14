import config
print("LANE_LABELS:", config.LANE_LABELS)
import pygame
import sys
import time
from enum import Enum, auto

from game_engine import GameEngine
from gesture_input import GestureInput
from renderer import Renderer
from config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT, COUNTDOWN_SECONDS


class GameState(Enum):
    MENU       = auto()
    COUNTDOWN  = auto()
    PLAYING    = auto()
    GAME_OVER  = auto()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gesture Rhythm Game")
    clock = pygame.time.Clock()

    engine        = GameEngine()
    gesture_input = GestureInput()
    renderer      = Renderer(screen)

    gesture_input.start()

    state              = GameState.MENU
    countdown_start    = 0.0   # 倒數開始時間（time.time()）

    running = True
    while running:

        # ── 事件處理 ──────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                # 任何狀態都能用 Q / ESC 離開
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

                # 主畫面：SPACE 或 ENTER 開始
                if state == GameState.MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        state           = GameState.COUNTDOWN
                        countdown_start = time.time()

                # 遊戲結束：R 重新開始，M 返回主畫面
                if state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        engine.reset()
                        state           = GameState.COUNTDOWN
                        countdown_start = time.time()
                        # gesture_input 已在執行中，不需重新 start
                    if event.key == pygame.K_m:
                        engine.reset()
                        gesture_input.stop()    # ✅ 回主畫面才關閉攝影機
                        state = GameState.MENU

        # ── 狀態更新與渲染 ────────────────────────────────
        if state == GameState.MENU:
            renderer.draw_menu()

        elif state == GameState.COUNTDOWN:
            elapsed  = time.time() - countdown_start
            remaining = COUNTDOWN_SECONDS - int(elapsed)

            if remaining <= 0:
                # 倒數結束 → 進入遊戲
                state = GameState.PLAYING
            else:
                renderer.draw_countdown(remaining)

        elif state == GameState.PLAYING:
            gesture = gesture_input.consume_gesture()
            engine.update(gesture)
            renderer.draw(engine)

            if engine.game_over:
                state = GameState.GAME_OVER

        elif state == GameState.GAME_OVER:
            # 繼續渲染最後一幀遊戲畫面 + Game Over 覆蓋層
            renderer.draw(engine)

        clock.tick(FPS)

    # ── 清理 ─────────────────────────────────────────────
    gesture_input.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()