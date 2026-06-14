import pygame
import os
from config import *


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame.font.init()
        self.font_title  = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_large  = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 32)
        self.font_small  = pygame.font.SysFont("Arial", 22)
        self.font_hint   = pygame.font.SysFont("Arial", 18)

        total_w = LANE_COUNT * LANE_WIDTH + (LANE_COUNT - 1) * LANE_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2
        self.lane_centers = [
            start_x + i * (LANE_WIDTH + LANE_GAP) + LANE_WIDTH // 2
            for i in range(LANE_COUNT)
        ]

        base = os.path.dirname(os.path.abspath(__file__))
        icon_files = ["3.png", "2.png", "1.png"]
        self.icons_large  = []
        self.icons_medium = []
        self.icons_small  = []

        for fname in icon_files:
            raw = pygame.image.load(os.path.join(base, fname)).convert_alpha()
            self.icons_large.append(pygame.transform.smoothscale(raw, (72, 72)))
            self.icons_medium.append(pygame.transform.smoothscale(raw, (48, 48)))
            self.icons_small.append(pygame.transform.smoothscale(raw, (36, 36)))

    def _blit_icon(self, icon_list: list, lane: int, cx: int, cy: int):
        icon = icon_list[lane]
        self.screen.blit(icon, (cx - icon.get_width() // 2,
                                cy - icon.get_height() // 2))

    def draw_menu(self):
        self.screen.fill(COLOR_BG)

        title = self.font_title.render("Gesture Rhythm", True, COLOR_PERFECT)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        sub = self.font_medium.render(
            "Control music blocks with your hand gestures", True, COLOR_DIM)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 178))

        self._draw_gesture_guide(y_start=260)

        prompt = self.font_medium.render("Press  SPACE  to Start", True, COLOR_TEXT)
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 550))

        quit_hint = self.font_hint.render("ESC / Q  to Quit", True, COLOR_DIM)
        self.screen.blit(quit_hint,
                         (SCREEN_WIDTH // 2 - quit_hint.get_width() // 2, 600))

        pygame.display.flip()

    def _draw_gesture_guide(self, y_start: int):
        card_w, card_h = 180, 210
        total_w = LANE_COUNT * card_w + (LANE_COUNT - 1) * LANE_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2

        desc_map = [
            ["Thumb up,", "others closed"],
            ["All five", "fingers open"],
            ["Index & middle", "fingers up"],
        ]

        for i in range(LANE_COUNT):
            cx_card   = start_x + i * (card_w + LANE_GAP)
            card_rect = pygame.Rect(cx_card, y_start, card_w, card_h)

            pygame.draw.rect(self.screen, (30, 30, 55), card_rect, border_radius=12)
            pygame.draw.rect(self.screen, LANE_COLORS[i], card_rect, 2, border_radius=12)

            self._blit_icon(self.icons_large, i, cx_card + card_w // 2, y_start + 46)

            lane_lbl = self.font_hint.render(f"Lane {i + 1}", True, LANE_COLORS[i])
            self.screen.blit(lane_lbl,
                             (cx_card + card_w // 2 - lane_lbl.get_width() // 2,
                              y_start + 98))

            name = self.font_small.render(LANE_LABELS[i], True, COLOR_TEXT)
            self.screen.blit(name,
                             (cx_card + card_w // 2 - name.get_width() // 2,
                              y_start + 122))

            for j, line in enumerate(desc_map[i]):
                desc = self.font_hint.render(line, True, COLOR_DIM)
                self.screen.blit(desc,
                                 (cx_card + card_w // 2 - desc.get_width() // 2,
                                  y_start + 152 + j * 22))

    def draw_countdown(self, remaining: int):
        self.screen.fill(COLOR_BG)

        ready = self.font_medium.render("Get ready...", True, COLOR_DIM)
        self.screen.blit(ready, (SCREEN_WIDTH // 2 - ready.get_width() // 2, 240))

        num = self.font_title.render(str(remaining), True, COLOR_PERFECT)
        self.screen.blit(num, (SCREEN_WIDTH // 2 - num.get_width() // 2, 300))

        hint = self.font_small.render(
            "Show your hand to the camera now", True, COLOR_TEXT)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 430))

        pygame.display.flip()

    def draw(self, engine):
        self.screen.fill(COLOR_BG)
        self._draw_lanes()
        self._draw_judge_line()
        self._draw_tiles(engine.tiles)
        self._draw_judge_results(engine.judge_results)
        self._draw_hud(engine)
        if engine.game_over:
            self._draw_game_over(engine)
        pygame.display.flip()

    def _draw_lanes(self):
        for i, cx in enumerate(self.lane_centers):
            rect = pygame.Rect(cx - LANE_WIDTH // 2, 0, LANE_WIDTH, SCREEN_HEIGHT)
            pygame.draw.rect(self.screen, (30, 30, 55), rect)
            pygame.draw.rect(self.screen, (60, 60, 100), rect, 2)

            self._blit_icon(self.icons_small, i, cx, SCREEN_HEIGHT - 52)

            label = self.font_hint.render(LANE_LABELS[i], True, LANE_COLORS[i])
            self.screen.blit(label, (cx - label.get_width() // 2, SCREEN_HEIGHT - 28))

    def _draw_judge_line(self):
        pygame.draw.line(self.screen, COLOR_JUDGE_LINE,
                         (0, JUDGE_LINE_Y), (SCREEN_WIDTH, JUDGE_LINE_Y), 3)
        label = self.font_hint.render("▼ Judge Line", True, COLOR_JUDGE_LINE)
        self.screen.blit(label, (10, JUDGE_LINE_Y - 24))

    def _draw_tiles(self, tiles):
        for tile in tiles:
            if tile.judged:
                continue
            cx   = self.lane_centers[tile.lane]
            rect = pygame.Rect(
                cx - LANE_WIDTH // 2 + 5,
                tile.y,
                LANE_WIDTH - 10,
                TILE_HEIGHT,
            )
            pygame.draw.rect(self.screen, LANE_COLORS[tile.lane], rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=10)

            self._blit_icon(self.icons_medium, tile.lane, cx,
                            tile.y + TILE_HEIGHT // 2)

    def _draw_judge_results(self, results):
        for jr in results:
            cx   = self.lane_centers[jr.lane]
            surf = self.font_large.render(jr.text, True, jr.color)
            surf.set_alpha(max(0, jr.alpha))
            self.screen.blit(surf, (cx - surf.get_width() // 2,
                                    JUDGE_LINE_Y - 80 + jr.y_offset))

    def _draw_hud(self, engine):
        score_surf = self.font_large.render(f"Score: {engine.score}", True, COLOR_TEXT)
        self.screen.blit(score_surf, (20, 20))

        if engine.combo >= 3:
            combo_surf = self.font_medium.render(
                f"x{engine.combo} Combo", True, COLOR_PERFECT)
            self.screen.blit(combo_surf, (20, 75))

        miss_surf = self.font_small.render(
            f"Miss: {engine.miss_count} / {engine.MAX_MISS}", True, COLOR_MISS)
        self.screen.blit(miss_surf, (SCREEN_WIDTH - 190, 20))

        spd_surf = self.font_hint.render(
            f"Speed: {engine.current_speed:.1f}", True, COLOR_DIM)
        self.screen.blit(spd_surf, (SCREEN_WIDTH - 190, 50))

    def _draw_game_over(self, engine):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        go_surf = self.font_large.render("GAME OVER", True, COLOR_MISS)
        self.screen.blit(go_surf, (SCREEN_WIDTH // 2 - go_surf.get_width() // 2, 210))

        score_surf = self.font_medium.render(
            f"Final Score: {engine.score}", True, COLOR_TEXT)
        self.screen.blit(score_surf,
                         (SCREEN_WIDTH // 2 - score_surf.get_width() // 2, 290))

        combo_surf = self.font_medium.render(
            f"Max Combo: {engine.max_combo}", True, COLOR_PERFECT)
        self.screen.blit(combo_surf,
                         (SCREEN_WIDTH // 2 - combo_surf.get_width() // 2, 340))

        r_surf = self.font_small.render("R  — Restart", True, COLOR_TEXT)
        self.screen.blit(r_surf, (SCREEN_WIDTH // 2 - r_surf.get_width() // 2, 420))

        m_surf = self.font_small.render("M  — Main Menu", True, COLOR_TEXT)
        self.screen.blit(m_surf, (SCREEN_WIDTH // 2 - m_surf.get_width() // 2, 455))

        q_surf = self.font_hint.render("ESC / Q  — Quit", True, COLOR_DIM)
        self.screen.blit(q_surf, (SCREEN_WIDTH // 2 - q_surf.get_width() // 2, 500))