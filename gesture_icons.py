import pygame


def draw_thumbs_up(surface, cx, cy, size, color):
    s, lw = size, max(2, size // 16)

    fist_w = int(s * 0.72)
    fist_h = int(s * 0.55)
    fist_x = cx - fist_w // 2
    fist_y = cy - fist_h // 4
    pygame.draw.rect(surface, color,
                     pygame.Rect(fist_x, fist_y, fist_w, fist_h),
                     lw, border_radius=int(s * 0.12))

    knuckle_y = fist_y + fist_h // 3
    gap = fist_w // 4
    for i in range(1, 4):
        x = fist_x + i * gap
        pygame.draw.line(surface, color, (x, fist_y + 2), (x, knuckle_y), lw)

    thumb_w = int(s * 0.22)
    thumb_h = int(s * 0.55)
    thumb_x = fist_x - thumb_w + int(s * 0.06)
    thumb_y = fist_y - thumb_h + int(s * 0.08)
    pygame.draw.rect(surface, color,
                     pygame.Rect(thumb_x, thumb_y, thumb_w, thumb_h),
                     lw, border_radius=int(s * 0.10))


def draw_open_palm(surface, cx, cy, size, color):
    s, lw = size, max(2, size // 16)

    finger_w   = int(s * 0.14)
    finger_gap = int(s * 0.04)
    heights    = [int(s * 0.38), int(s * 0.52), int(s * 0.58),
                  int(s * 0.52), int(s * 0.44)]
    total_fw   = 5 * finger_w + 4 * finger_gap
    fx_start   = cx - total_fw // 2
    palm_top_y = cy + int(s * 0.08)
    palm_h     = int(s * 0.30)

    for i, h in enumerate(heights):
        fx = fx_start + i * (finger_w + finger_gap)
        pygame.draw.rect(surface, color,
                         pygame.Rect(fx, palm_top_y - h, finger_w, h),
                         lw, border_radius=finger_w // 2)

    pad = int(s * 0.06)
    pygame.draw.polygon(surface, color, [
        (fx_start - pad,             palm_top_y),
        (fx_start + total_fw + pad,  palm_top_y),
        (fx_start + total_fw,        palm_top_y + palm_h),
        (fx_start,                   palm_top_y + palm_h),
    ], lw)
    pygame.draw.line(surface, color,
                     (fx_start - pad, palm_top_y),
                     (fx_start + total_fw + pad, palm_top_y), lw * 2)


def draw_scissors(surface, cx, cy, size, color):
    """
    ✌️ 剪刀手
    結構：握拳底座 + 食指與中指向上伸直（兩條分開的手指）
    """
    s, lw = size, max(2, size // 16)

    # ── 握拳底座 ──
    fist_w = int(s * 0.68)
    fist_h = int(s * 0.40)
    fist_x = cx - fist_w // 2
    fist_y = cy + int(s * 0.05)
    pygame.draw.rect(surface, color,
                     pygame.Rect(fist_x, fist_y, fist_w, fist_h),
                     lw, border_radius=int(s * 0.10))

    # ── 食指（左）──
    idx_w  = int(s * 0.15)
    idx_h  = int(s * 0.52)
    idx_x  = cx - int(s * 0.18)
    idx_y  = fist_y - idx_h + lw
    pygame.draw.rect(surface, color,
                     pygame.Rect(idx_x, idx_y, idx_w, idx_h),
                     lw, border_radius=idx_w // 2)

    # ── 中指（右）──
    mid_w  = int(s * 0.15)
    mid_h  = int(s * 0.56)   # 中指略長
    mid_x  = cx + int(s * 0.04)
    mid_y  = fist_y - mid_h + lw
    pygame.draw.rect(surface, color,
                     pygame.Rect(mid_x, mid_y, mid_w, mid_h),
                     lw, border_radius=mid_w // 2)

    # ── 拇指側邊小突起 ──
    thumb_w = int(s * 0.16)
    thumb_h = int(s * 0.18)
    thumb_x = fist_x - thumb_w + lw * 2
    thumb_y = fist_y + int(s * 0.08)
    pygame.draw.rect(surface, color,
                     pygame.Rect(thumb_x, thumb_y, thumb_w, thumb_h),
                     lw, border_radius=int(s * 0.06))


# ✅ 保留 draw_fist 供未來需要（例如待機提示圖示）
def draw_fist(surface, cx, cy, size, color):
    s, lw = size, max(2, size // 16)

    fist_w = int(s * 0.72)
    fist_h = int(s * 0.60)
    fist_x = cx - fist_w // 2
    fist_y = cy - fist_h // 2 + int(s * 0.05)
    pygame.draw.rect(surface, color,
                     pygame.Rect(fist_x, fist_y, fist_w, fist_h),
                     lw, border_radius=int(s * 0.12))

    knuckle_w   = fist_w // 4 - lw
    knuckle_h   = int(s * 0.14)
    total_kw    = 4 * knuckle_w + 3 * lw
    kx_start    = cx - total_kw // 2
    ky          = fist_y - knuckle_h + lw
    for i in range(4):
        kx = kx_start + i * (knuckle_w + lw)
        pygame.draw.rect(surface, color,
                         pygame.Rect(kx, ky, knuckle_w, knuckle_h),
                         lw, border_radius=int(s * 0.06))

    thumb_w = int(s * 0.18)
    thumb_h = int(s * 0.22)
    pygame.draw.rect(surface, color,
                     pygame.Rect(fist_x - thumb_w + lw * 2,
                                 fist_y + int(s * 0.10), thumb_w, thumb_h),
                     lw, border_radius=int(s * 0.08))