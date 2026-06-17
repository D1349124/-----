import pygame
import os
from config import *

# ── Game Boy 色盤 ──────────────────────────────
GB_0 = (13,  26,  13)   # 最深：背景
GB_1 = (26,  51,  32)   # 深：面板底色
GB_2 = (45,  90,  61)   # 中：邊框/軌道
GB_3 = (74, 140,  92)   # 亮：強調/填充
GB_4 = (184, 216, 176)  # 最亮：文字/高亮
GB_5 = (232, 240, 224)  # 近白：最高亮文字

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PressStart2P-Regular.ttf")


def _px(surface, color, rect, border=0, inner=False):
    """畫像素風格矩形：外框 + 可選雙層內框"""
    if border == 0:
        pygame.draw.rect(surface, color, rect)
    else:
        pygame.draw.rect(surface, GB_1, rect)
        pygame.draw.rect(surface, color, rect, border)
        if inner:
            ir = pygame.Rect(rect.x + border + 1, rect.y + border + 1,
                             rect.width - (border + 1) * 2,
                             rect.height - (border + 1) * 2)
            pygame.draw.rect(surface, GB_2, ir, 1)


class Button:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.font = font

    def draw(self, surface: pygame.Surface, mouse_pos: tuple) -> None:
        is_hover = self.rect.collidepoint(mouse_pos)
        bg       = GB_2 if is_hover else GB_1
        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, GB_3, self.rect, 3)
        ir = pygame.Rect(self.rect.x + 4, self.rect.y + 4,
                         self.rect.width - 8, self.rect.height - 8)
        pygame.draw.rect(surface, GB_2 if is_hover else GB_1, ir, 1)
        label = self.font.render(self.text, False, GB_4 if is_hover else GB_3)
        surface.blit(label, (self.rect.centerx - label.get_width() // 2,
                              self.rect.centery - label.get_height() // 2))

    def is_clicked(self, mouse_pos: tuple, mouse_click: bool) -> bool:
        return mouse_click and self.rect.collidepoint(mouse_pos)


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame.font.init()

        # Press Start 2P 字體，多個尺寸
        self.font_title  = pygame.font.Font(FONT_PATH, 50)
        self.font_large  = pygame.font.Font(FONT_PATH, 14)
        self.font_medium = pygame.font.Font(FONT_PATH, 11)
        self.font_small  = pygame.font.Font(FONT_PATH, 15)
        self.font_hint   = pygame.font.Font(FONT_PATH, 9)
        self.font_rank   = pygame.font.Font(FONT_PATH, 120)
        self.font_val   = pygame.font.Font(FONT_PATH, 20)
        

        total_w = LANE_COUNT * LANE_WIDTH + (LANE_COUNT - 1) * LANE_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2
        self.lane_centers = [
            start_x + i * (LANE_WIDTH + LANE_GAP) + LANE_WIDTH // 2
            for i in range(LANE_COUNT)
        ]

        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        icon_files = ["3.png", "2.png", "1.png"]
        self.icons_large  = []
        self.icons_medium = []
        self.icons_small  = []
        for fname in icon_files:
            raw = pygame.image.load(os.path.join(base, fname)).convert_alpha()
            # 轉綠色調
            self.icons_large.append(
                self._tint(pygame.transform.smoothscale(raw, (56, 56))))
            self.icons_medium.append(
                self._tint(pygame.transform.smoothscale(raw, (40, 40))))
            self.icons_small.append(
                self._tint(pygame.transform.smoothscale(raw, (28, 28))))

        self._btn_back = Button(
            pygame.Rect(12, 12, 96, 28), "< BACK", self.font_hint)

    def _tint(self, surf: pygame.Surface) -> pygame.Surface:
        """把圖片染成 GB 綠色調"""
        tinted = surf.copy()
        tinted.fill(GB_3, special_flags=pygame.BLEND_RGB_MULT)
        return tinted

    def _blit_icon(self, icon_list, lane, cx, cy):
        icon = icon_list[lane]
        self.screen.blit(icon, (cx - icon.get_width() // 2,
                                cy - icon.get_height() // 2))

    def _win_border(self, rect: pygame.Rect, title: str = ""):
        """畫像素風格視窗邊框"""
        pygame.draw.rect(self.screen, GB_1, rect)
        pygame.draw.rect(self.screen, GB_3, rect, 3)
        inner = pygame.Rect(rect.x + 4, rect.y + 4,
                            rect.width - 8, rect.height - 8)
        pygame.draw.rect(self.screen, GB_2, inner, 1)
        if title:
            t = self.font_hint.render(title, False, GB_4)
            self.screen.blit(t, (rect.x + 8, rect.y + 8))

    def _pixel_bar(self, x: int, y: int, w: int, h: int,
                   fill: float, color_fill=GB_3, color_bg=GB_1):
        """像素格子進度條"""
        seg   = h + 2
        count = w // seg
        pygame.draw.rect(self.screen, GB_0,
                         pygame.Rect(x, y, w, h))
        pygame.draw.rect(self.screen, GB_2,
                         pygame.Rect(x, y, w, h), 2)
        filled = int(count * fill)
        for i in range(count):
            c = color_fill if i < filled else color_bg
            pygame.draw.rect(self.screen, c,
                             pygame.Rect(x + 2 + i * seg, y + 2,
                                         h - 2, h - 4))

    def _hline(self, y: int, color=GB_2):
        pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))

    # ══════════════════════════════════════
    #  主畫面
    # ══════════════════════════════════════

    def draw_menu(self, mouse_pos: tuple, mouse_click: bool) -> str | None:
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        # 主視窗
        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect, "GESTURE RHYTHM v1.0")

        title = self.font_title.render("GESTURE", False, GB_4)
        sub   = self.font_title.render("RHYTHM", False, GB_3)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 55))
        self.screen.blit(sub,   (SCREEN_WIDTH // 2 - sub.get_width() // 2,   120))

        # 分隔線
        self._pixel_divider(190)

        # 手勢說明（y_start 往下移）
        self._draw_gesture_guide(y_start=200)

        self._pixel_divider(450)

        # 按鈕
        btn_start = Button(
            pygame.Rect(SCREEN_WIDTH // 2 - 220, 470, 180, 40),
            "START", self.font_small)
        btn_settings = Button(
            pygame.Rect(SCREEN_WIDTH // 2 + 40, 470, 180, 40),
            "SETTINGS", self.font_small)
        btn_start.draw(self.screen, mouse_pos)
        btn_settings.draw(self.screen, mouse_pos)

        hint = self.font_hint.render("ESC: QUIT", False, GB_2)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 530))

        pygame.display.flip()

        if btn_start.is_clicked(mouse_pos, mouse_click):
            return "start"
        if btn_settings.is_clicked(mouse_pos, mouse_click):
            return "settings"
        return None

    def _draw_pixel_grid(self):
        """背景像素點陣"""
        for x in range(0, SCREEN_WIDTH, 8):
            for y in range(0, SCREEN_HEIGHT, 8):
                pygame.draw.rect(self.screen, GB_1,
                                 pygame.Rect(x, y, 1, 1))

    def _pixel_divider(self, y: int):
        """像素虛線分隔"""
        for x in range(32, SCREEN_WIDTH - 32, 12):
            pygame.draw.rect(self.screen, GB_2,
                             pygame.Rect(x, y, 8, 2))

    def _draw_gesture_guide(self, y_start: int):
        card_w = 200
        gap    = 30
        total  = LANE_COUNT * card_w + (LANE_COUNT - 1) * gap
        sx     = (SCREEN_WIDTH - total) // 2
        labels = ["THUMBS UP", "OPEN PALM", "SCISSORS"]
        descs  = ["THUMB UP\nOTHERS CLOSED",
                  "ALL FINGERS\nOPEN",
                  "INDEX+MIDDLE\nFINGERS UP"]

        for i in range(LANE_COUNT):
            cx      = sx + i * (card_w + gap)
            card    = pygame.Rect(cx, y_start, card_w, 240)
            self._win_border(card, f"LANE {i + 1}")

            # 圖示
            self._blit_icon(self.icons_large, i,
                            cx + card_w // 2, y_start + 90)

            # 名稱
            name = self.font_small.render(labels[i], False, GB_4)
            self.screen.blit(name,
                            (cx + card_w // 2 - name.get_width() // 2,
                            y_start + 150))

            for j, line in enumerate(descs[i].split("\n")):
                d = self.font_hint.render(line, False, GB_3)
                self.screen.blit(d,
                                (cx + card_w // 2 - d.get_width() // 2,
                                y_start + 174 + j * 16))      

    # ══════════════════════════════════════
    #  Settings 畫面
    # ══════════════════════════════════════

    def draw_settings(self, volume: float,
                      mouse_pos: tuple, mouse_click: bool):
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect, "SETTINGS")

        if self._btn_back.is_clicked(mouse_pos, mouse_click):
            pygame.display.flip()
            return "back"
        self._btn_back.draw(self.screen, mouse_pos)

        label = self.font_medium.render("MUSIC VOLUME", False, GB_4)
        self.screen.blit(label,
                         (SCREEN_WIDTH // 2 - label.get_width() // 2, 160))

        pct = self.font_large.render(f"{int(volume * 100):03d}%", False, GB_5)
        self.screen.blit(pct,
                         (SCREEN_WIDTH // 2 - pct.get_width() // 2, 185))

        # 像素進度條
        bar_w = 480
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 230
        self._pixel_bar(bar_x, bar_y, bar_w, 16, volume)

        btn_minus = Button(pygame.Rect(bar_x - 56, bar_y - 4, 44, 24),
                           "<<", self.font_hint)
        btn_plus  = Button(pygame.Rect(bar_x + bar_w + 12, bar_y - 4, 44, 24),
                           ">>", self.font_hint)
        btn_minus.draw(self.screen, mouse_pos)
        btn_plus.draw(self.screen, mouse_pos)

        hint = self.font_hint.render("CLICK BAR OR USE << >>", False, GB_2)
        self.screen.blit(hint,
                         (SCREEN_WIDTH // 2 - hint.get_width() // 2, 262))

        pygame.display.flip()

        new_volume = None
        bar_rect = pygame.Rect(bar_x, bar_y - 8, bar_w, 32)
        if mouse_click and bar_rect.collidepoint(mouse_pos):
            new_volume = max(0.0, min(1.0,
                            (mouse_pos[0] - bar_x) / bar_w))
        if btn_minus.is_clicked(mouse_pos, mouse_click):
            new_volume = max(0.0, round(volume - 0.05, 2))
        if btn_plus.is_clicked(mouse_pos, mouse_click):
            new_volume = min(1.0, round(volume + 0.05, 2))
        return new_volume

    # ══════════════════════════════════════
    #  選歌畫面
    # ══════════════════════════════════════

    def draw_song_select(self, song_list: list, selected: str | None,
                         scroll: int, mouse_pos: tuple,
                         mouse_click: bool) -> str | None:
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect)
        t = self.font_hint.render("SELECT SONG", False, GB_4)
        self.screen.blit(t, (main_rect.x + 25, main_rect.y + 8))
        if self._btn_back.is_clicked(mouse_pos, mouse_click):
            pygame.display.flip()
            return "back"
        self._btn_back.draw(self.screen, mouse_pos)

        btn_import = Button(
            pygame.Rect(SCREEN_WIDTH - 220, 12, 196, 36),
            "+ IMPORT SONG", self.font_hint
        )
        if btn_import.is_clicked(mouse_pos, mouse_click):
            pygame.display.flip()
            return "import"
        btn_import.draw(self.screen, mouse_pos)

        if not song_list:
            msg = self.font_small.render('NO MP3 IN music/', False, GB_3)
            self.screen.blit(msg,
                             (SCREEN_WIDTH // 2 - msg.get_width() // 2, 300))
            pygame.display.flip()
            return None

        item_h     = 44
        list_x     = 48
        list_w     = SCREEN_WIDTH - 96
        list_top   = 56
        list_bot   = SCREEN_HEIGHT - 56
        visible    = (list_bot - list_top) // item_h
        max_scroll = max(0, len(song_list) - visible)
        scroll     = min(scroll, max_scroll)
        clicked_song = None

        for idx in range(visible):
            song_idx = idx + scroll
            if song_idx >= len(song_list):
                break
            song        = song_list[song_idx]
            iy          = list_top + idx * item_h
            rect        = pygame.Rect(list_x, iy + 2, list_w, item_h - 4)
            is_selected = (song == selected)
            is_hover    = rect.collidepoint(mouse_pos)

            bg = GB_2 if is_selected else (GB_1 if is_hover else GB_0)
            pygame.draw.rect(self.screen, bg, rect)
            pygame.draw.rect(self.screen,
                             GB_4 if is_selected else GB_2, rect, 2)
            if is_selected:
                ir = pygame.Rect(rect.x + 3, rect.y + 3,
                                 rect.width - 6, rect.height - 6)
                pygame.draw.rect(self.screen, GB_3, ir, 1)

            # 左側像素色條
            pygame.draw.rect(self.screen, GB_3,
                             pygame.Rect(list_x, iy + 2, 4, item_h - 4))

            display_name = os.path.splitext(song)[0].upper()
            name_surf = self.font_small.render(
                display_name, False, GB_5 if is_selected else GB_3)
            self.screen.blit(name_surf,
                             (list_x + 12,
                              iy + item_h // 2 - name_surf.get_height() // 2))

            if is_selected:
                mark = self.font_hint.render("> SELECTED <", False, GB_4)
                self.screen.blit(mark,
                                 (rect.right - mark.get_width() - 10,
                                  iy + item_h // 2 - mark.get_height() // 2))

            if mouse_click and is_hover:
                clicked_song = song

        if max_scroll > 0:
            hint = self.font_hint.render(
                f"{scroll + 1}-{min(scroll + visible, len(song_list))}/{len(song_list)}",
                False, GB_2)
            self.screen.blit(hint,
                             (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                              SCREEN_HEIGHT - 28))

        pygame.display.flip()
        return clicked_song

    # ══════════════════════════════════════
    #  難度選擇畫面
    # ══════════════════════════════════════

    def draw_difficulty(self, selected: str, mouse_pos: tuple,
                        mouse_click: bool) -> str | None:
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect)
        t = self.font_hint.render("SELECT DIFFICULTY", False, GB_4)
        self.screen.blit(t, (main_rect.x + 25, main_rect.y + 8))
        if self._btn_back.is_clicked(mouse_pos, mouse_click):
            pygame.display.flip()
            return "back"
        self._btn_back.draw(self.screen, mouse_pos)

        diff_settings = {
            "Easy":   {"desc": ["3.0 SPEED", "15 MISS LIMIT"]},
            "Normal": {"desc": ["4.0 SPEED", "10 MISS LIMIT"]},
            "Hard":   {"desc": ["6.0 SPEED", "5  MISS LIMIT"]},
        }
        card_w, card_h = 220, 260
        gap     = 36
        total_w = len(diff_settings) * card_w + (len(diff_settings) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        card_y  = 145
        clicked = None

        for idx, (name, cfg) in enumerate(diff_settings.items()):
            cx      = start_x + idx * (card_w + gap)
            rect    = pygame.Rect(cx, card_y, card_w, card_h)
            is_sel  = (name == selected)
            is_hov  = rect.collidepoint(mouse_pos)

            pygame.draw.rect(self.screen, GB_2 if is_sel else GB_1, rect)
            pygame.draw.rect(self.screen,
                             GB_4 if is_sel else GB_3, rect, 3)
            ir = pygame.Rect(cx + 4, card_y + 4, card_w - 8, card_h - 8)
            pygame.draw.rect(self.screen,
                             GB_3 if is_sel else GB_2, ir, 1)

            name_surf = self.font_large.render(name.upper(), False,
                                                GB_5 if is_sel else GB_3)
            self.screen.blit(name_surf,
                            (cx + card_w // 2 - name_surf.get_width() // 2,
                            card_y + 32))    # 24 → 32

            # 像素分隔線
            for px in range(cx + 8, cx + card_w - 8, 6):
                pygame.draw.rect(self.screen, GB_2,
                                pygame.Rect(px, card_y + 70, 4, 2))   # 56 → 70

            for j, line in enumerate(cfg["desc"]):
                d = self.font_small.render(line, False,
                                        GB_4 if is_sel else GB_2)
                self.screen.blit(d,
                                (cx + card_w // 2 - d.get_width() // 2,
                                card_y + 90 + j * 24))   # 72+20 → 90+24

            # 選中指示器
            for px in range(3):
                pygame.draw.rect(
                    self.screen, GB_4,
                    pygame.Rect(cx + card_w // 2 - 12 + px * 10,
                                card_y + card_h - 24, 8, 8))   # -20 → -24

            if is_hov and not is_sel:
                s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                s.fill((184, 216, 176, 20))
                self.screen.blit(s, (cx, card_y))

            if mouse_click and is_hov:
                clicked = name

        btn_confirm = Button(
            pygame.Rect(SCREEN_WIDTH // 2 - 100, 400, 200, 44),   # 356→400, 40→44
            "CONFIRM", self.font_small)

        hint = self.font_hint.render(
            f"SELECTED: {selected.upper()}", False, GB_2)
        self.screen.blit(hint,
                        (SCREEN_WIDTH // 2 - hint.get_width() // 2, 458))   # 408→458

        pygame.display.flip()

        if btn_confirm.is_clicked(mouse_pos, mouse_click):
            return selected
        if clicked:
            return clicked
        return None

    # ══════════════════════════════════════
    #  倒數畫面
    # ══════════════════════════════════════

    def draw_countdown(self, remaining: int):
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect)

        ready = self.font_medium.render("GET READY", False, GB_3)
        self.screen.blit(ready,
                         (SCREEN_WIDTH // 2 - ready.get_width() // 2, 220))

        # 大數字（像素風格）
        num = self.font_title.render(str(remaining), False, GB_5)
        # 畫陰影
        shadow = self.font_title.render(str(remaining), False, GB_2)
        self.screen.blit(shadow,
                         (SCREEN_WIDTH // 2 - num.get_width() // 2 + 3, 283))
        self.screen.blit(num,
                         (SCREEN_WIDTH // 2 - num.get_width() // 2, 280))

        hint = self.font_hint.render(
            "SHOW YOUR HAND TO CAMERA", False, GB_2)
        self.screen.blit(hint,
                         (SCREEN_WIDTH // 2 - hint.get_width() // 2, 380))

        pygame.display.flip()
    def draw_importing(self):
        """匯入新歌分析中的等待畫面，帶轉動動畫"""
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect)

        title = self.font_medium.render("IMPORTING SONG", False, GB_4)
        self.screen.blit(title,
                        (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))

        # 像素風格 loading 動畫（依時間轉動的方塊）
        tick = (pygame.time.get_ticks() // 200) % 4
        dots = "." * (tick + 1)
        msg = self.font_small.render(f"ANALYZING{dots}", False, GB_3)
        self.screen.blit(msg,
                        (SCREEN_WIDTH // 2 - msg.get_width() // 2, 260))

        # 像素方塊轉圈動畫
        cx, cy, r = SCREEN_WIDTH // 2, 340, 40
        positions = [(0,-1), (1,0), (0,1), (-1,0)]
        active = (pygame.time.get_ticks() // 150) % 4
        for i, (dx, dy) in enumerate(positions):
            color = GB_5 if i == active else GB_2
            pygame.draw.rect(self.screen, color,
                            pygame.Rect(cx + dx*r - 8, cy + dy*r - 8, 16, 16))

        hint = self.font_hint.render(
            "THIS MAY TAKE A FEW SECONDS...", False, GB_2)
        self.screen.blit(hint,
                        (SCREEN_WIDTH // 2 - hint.get_width() // 2, 420))

        pygame.display.flip()

    # ══════════════════════════════════════
    #  遊戲主畫面
    # ══════════════════════════════════════

    def draw(self, engine, progress: float = 0.0):
        self.screen.fill(GB_0)
        self._draw_pixel_grid()
        self._draw_lanes()
        self._draw_judge_line()
        self._draw_tiles(engine.tiles)
        self._draw_judge_results(engine.judge_results)
        self._draw_hud(engine)
        self._draw_progress_bar(progress)
        pygame.display.flip()

    def _draw_lanes(self):
        for i, cx in enumerate(self.lane_centers):
            # 軌道背景
            lane_rect = pygame.Rect(cx - LANE_WIDTH // 2, 0,
                                    LANE_WIDTH, SCREEN_HEIGHT)
            s = pygame.Surface((LANE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((*GB_1, 120))
            self.screen.blit(s, lane_rect.topleft)

            # 左右邊線（雙線像素風）
            pygame.draw.line(self.screen, GB_2,
                             (cx - LANE_WIDTH // 2, 0),
                             (cx - LANE_WIDTH // 2, SCREEN_HEIGHT), 2)
            pygame.draw.line(self.screen, GB_1,
                             (cx - LANE_WIDTH // 2 + 3, 0),
                             (cx - LANE_WIDTH // 2 + 3, SCREEN_HEIGHT), 1)
            pygame.draw.line(self.screen, GB_2,
                             (cx + LANE_WIDTH // 2, 0),
                             (cx + LANE_WIDTH // 2, SCREEN_HEIGHT), 2)
            pygame.draw.line(self.screen, GB_1,
                             (cx + LANE_WIDTH // 2 - 3, 0),
                             (cx + LANE_WIDTH // 2 - 3, SCREEN_HEIGHT), 1)

            # 底部圖示 + 標籤
            self._blit_icon(self.icons_small, i, cx, SCREEN_HEIGHT - 44)
            label = self.font_hint.render(
                LANE_LABELS[i].upper(), False, GB_3)
            self.screen.blit(label,
                             (cx - label.get_width() // 2,
                              SCREEN_HEIGHT - 18))

    def _draw_judge_line(self):
        y = JUDGE_LINE_Y
        # 主線（3px）
        pygame.draw.line(self.screen, GB_4, (0, y), (SCREEN_WIDTH, y), 3)
        # 上下輔助線
        pygame.draw.line(self.screen, GB_2, (0, y - 2), (SCREEN_WIDTH, y - 2), 1)
        pygame.draw.line(self.screen, GB_2, (0, y + 3), (SCREEN_WIDTH, y + 3), 1)
        # 刻度標記
        for cx in self.lane_centers:
            pygame.draw.rect(self.screen, GB_5,
                             pygame.Rect(cx - 4, y - 6, 8, 14))
            pygame.draw.rect(self.screen, GB_3,
                             pygame.Rect(cx - 2, y - 4, 4, 10))

    def _draw_tiles(self, tiles):
        for tile in tiles:
            if tile.judged:
                continue
            cx   = self.lane_centers[tile.lane]
            rect = pygame.Rect(cx - LANE_WIDTH // 2 + 6, tile.y,
                               LANE_WIDTH - 12, TILE_HEIGHT)

            # 填色
            pygame.draw.rect(self.screen, GB_2, rect)
            # 外框（3px）
            pygame.draw.rect(self.screen, GB_4, rect, 3)
            # 內框（1px）
            ir = pygame.Rect(rect.x + 4, rect.y + 4,
                             rect.width - 8, rect.height - 8)
            pygame.draw.rect(self.screen, GB_3, ir, 1)

            # 圖示
            self._blit_icon(self.icons_medium, tile.lane, cx,
                            tile.y + TILE_HEIGHT // 2)

    def _draw_judge_results(self, results):
        for jr in results:
            cx   = self.lane_centers[jr.lane]
            # 陰影
            shadow = self.font_medium.render(jr.text, False, GB_1)
            shadow.set_alpha(max(0, jr.alpha))
            surf   = self.font_medium.render(jr.text, False, GB_5)
            surf.set_alpha(max(0, jr.alpha))
            y = JUDGE_LINE_Y - 60 + jr.y_offset
            self.screen.blit(shadow, (cx - surf.get_width() // 2 + 2, y + 2))
            self.screen.blit(surf,   (cx - surf.get_width() // 2, y))

    def _draw_hud(self, engine):
        # 頂部 HUD 條
        pygame.draw.rect(self.screen, GB_1,
                        pygame.Rect(0, 0, SCREEN_WIDTH, 36))
        pygame.draw.line(self.screen, GB_3,
                        (0, 35), (SCREEN_WIDTH, 35), 2)
        pygame.draw.line(self.screen, GB_2,
                        (0, 37), (SCREEN_WIDTH, 37), 1)

        # 分隔格線
        for x in [200, 370, 520]:
            pygame.draw.line(self.screen, GB_2, (x, 0), (x, 36), 1)

        # SCORE
        score_l = self.font_hint.render("SCORE", False, GB_2)
        score_v = self.font_small.render(
            f"{engine.score:06d}", False, GB_4)
        self.screen.blit(score_l, (12, 4))
        self.screen.blit(score_v, (12, 18))

        # COMBO
        if engine.combo >= 3:
            combo_l = self.font_hint.render("COMBO", False, GB_2)
            combo_v = self.font_small.render(
                f"x{engine.combo:02d}", False, GB_5)
            self.screen.blit(combo_l, (210, 4))
            self.screen.blit(combo_v, (210, 18))

        # MISS
        miss_l = self.font_hint.render("MISS", False, GB_2)
        miss_v = self.font_small.render(
            f"{engine.miss_count}/{engine.MAX_MISS}", False, GB_3)
        self.screen.blit(miss_l, (380, 4))
        self.screen.blit(miss_v, (380, 18))

        # SPEED
        spd_l = self.font_hint.render("SPD", False, GB_2)
        spd_v = self.font_hint.render(
            f"{engine.current_speed:.1f}", False, GB_2)
        self.screen.blit(spd_l, (530, 4))
        self.screen.blit(spd_v, (530, 18))


    def _draw_progress_bar(self, progress: float):
        """畫面最上方的歌曲進度條"""
        bar_h = 4
        bar_y = 36
        pygame.draw.rect(self.screen, GB_1,
                        pygame.Rect(0, bar_y, SCREEN_WIDTH, bar_h))
        fill_w = int(SCREEN_WIDTH * max(0.0, min(1.0, progress)))
        pygame.draw.rect(self.screen, GB_4,
                        pygame.Rect(0, bar_y, fill_w, bar_h))
        seg = 10
        for x in range(0, fill_w, seg):
            pygame.draw.rect(self.screen, GB_3,
                            pygame.Rect(x, bar_y, 2, bar_h))

    # ══════════════════════════════════════
    #  Game Over 畫面
    # ══════════════════════════════════════

    def draw_game_over(self, engine, rank: str, record: dict | None,
                       mouse_pos: tuple, mouse_click: bool) -> str | None:
        self.screen.fill(GB_0)
        self._draw_pixel_grid()

        main_rect = pygame.Rect(24, 20, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 40)
        self._win_border(main_rect, "RESULT")

        # 大 Rank 字（像素陰影）
        rank_surf   = self.font_rank.render(rank, False, GB_5)
        rank_shadow = self.font_rank.render(rank, False, GB_2)
        rx = SCREEN_WIDTH // 4 - rank_surf.get_width() // 2
        self.screen.blit(rank_shadow, (rx + 15, 104))
        self.screen.blit(rank_surf,   (rx+11, 100))
        # 垂直像素分隔線
        for y in range(60, 500, 6):
            pygame.draw.rect(self.screen, GB_2,
                             pygame.Rect(SCREEN_WIDTH // 2 - 16, y, 4, 4))

        # 右側統計
        rx2   = SCREEN_WIDTH // 2
        ry    = 64
        gap   = 44
        stats = [
            ("SCORE",     f"{engine.score:06d}"),
            ("MAX COMBO", f"x{engine.max_combo:02d}"),
            ("PERFECT",   str(engine.perfect_count)),
            ("GOOD",      str(engine.good_count)),
            ("MISS",      str(engine.miss_count)),
        ]

        for i, (label, value) in enumerate(stats):
            lbl = self.font_val.render(label, False, GB_2)
            val = self.font_val.render(value, False, GB_4)
            self.screen.blit(lbl, (rx2, ry + i * gap))
            self.screen.blit(val, (rx2 + 220, ry + i * gap))
            # 像素分隔線
            if i < len(stats) - 1:
                for px in range(rx2, rx2 + 320, 8):
                    pygame.draw.rect(self.screen, GB_1,
                                     pygame.Rect(px, ry + i * gap + 34, 4, 2))

        # Best score
        if record:
            by = ry + len(stats) * gap + 8
            for px in range(rx2, rx2 + 320, 6):
                pygame.draw.rect(self.screen, GB_2,
                                 pygame.Rect(px, by - 4, 4, 2))
            lbl = self.font_val.render("BEST", False, GB_2)
            val = self.font_val.render(str(record["score"]), False, GB_3)
            self.screen.blit(lbl, (rx2, by + 4))
            self.screen.blit(val, (rx2 + 220, by + 4))
            if engine.score >= record["score"]:
                nb = self.font_val.render("* NEW BEST *", False, GB_4)
                self.screen.blit(nb, (rx2, by + 22))

        # 按鈕
        btn_restart = Button(
            pygame.Rect(SCREEN_WIDTH // 4 - 45, 500, 180, 36),
            "RESTART", self.font_val)
        btn_menu = Button(
            pygame.Rect(SCREEN_WIDTH // 2 + 95, 500, 140, 36),
            "MENU", self.font_val)
        btn_restart.draw(self.screen, mouse_pos)
        btn_menu.draw(self.screen, mouse_pos)

        pygame.display.flip()

        if btn_restart.is_clicked(mouse_pos, mouse_click):
            return "restart"
        if btn_menu.is_clicked(mouse_pos, mouse_click):
            return "menu"
        return None

    # ══════════════════════════════════════
    #  暫停畫面
    # ══════════════════════════════════════

    def draw_pause(self, mouse_pos: tuple, mouse_click: bool) -> str | None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*GB_0, 210))
        self.screen.blit(overlay, (0, 0))

        # 像素點陣遮罩
        for x in range(0, SCREEN_WIDTH, 4):
            for y in range(0, SCREEN_HEIGHT, 4):
                pygame.draw.rect(self.screen, (*GB_0, 80),
                                 pygame.Rect(x, y, 2, 2))

        win = pygame.Rect(SCREEN_WIDTH // 2 - 220, 100, 440, 440)  # 160,140,320,300 → 220,100,440,440
        self._win_border(win, "PAUSED")

        btns = [
            ("CONTINUE", "continue"),
            ("SETTINGS", "settings"),
            ("RESTART",  "restart"),
            ("HOME",     "home"),
        ]
        btn_h   = 52       # 36 → 52
        btn_gap = 16       # 10 → 16
        start_y = 160      # 188 → 160
        result  = None

        for i, (label, key) in enumerate(btns):
            by  = start_y + i * (btn_h + btn_gap)
            btn = Button(
                pygame.Rect(SCREEN_WIDTH // 2 - 160, by, 320, btn_h),  # 120,240 → 160,320
                label, self.font_large)   # font_hint → font_small
            btn.draw(self.screen, mouse_pos)
            if btn.is_clicked(mouse_pos, mouse_click):
                result = key

        hint = self.font_hint.render("ESC: RESUME", False, GB_2)
        self.screen.blit(hint,
                        (SCREEN_WIDTH // 2 - hint.get_width() // 2, 490))  # 418 → 490
        pygame.display.flip()
        return result