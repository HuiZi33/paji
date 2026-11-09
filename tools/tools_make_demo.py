# -*- coding: utf-8 -*-
"""生成 README 用的演示 GIF（纯代码合成，无需录屏）。

剧情：照片卡片出现 → emoji 从空中「啪」地落上去 → 变换框出现并旋转
      → 高亮「导出」→ 结束
产物：demo.gif
"""
import math
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from tools_make_intro import find_photo_rect, emoji, font, load

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
W, H = 880, 560
FPS = 14
CARD = 440
CARD_X, CARD_Y = 48, 60


def ease_out_back(t, s=1.7):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t


def rounded(img, radius):
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1],
                                           radius=radius, fill=255)
    out = img.copy()
    out.putalpha(ImageChops.multiply(out.split()[3], mask))
    return out


def bg_image():
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(20 + 20 * t), int(22 + 14 * t), int(38 + 40 * t)))
    return img.convert('RGBA')


def draw_cursor(d, x, y, scale=1.0):
    s = 16 * scale
    pts = [(x, y), (x, y + s), (x + s * 0.32, y + s * 0.74),
           (x + s * 0.62, y + s * 1.02), (x + s * 0.78, y + s * 0.9),
           (x + s * 0.5, y + s * 0.64), (x + s * 0.86, y + s * 0.6)]
    d.polygon(pts, fill=(245, 246, 250, 255), outline=(30, 30, 36, 255))
    d.polygon([(x + 2, y + 2), (x + 2, y + s * 0.72), (x + s * 0.3, y + s * 0.55)],
              fill=(30, 30, 36, 255))


def sel_box(img, cx, cy, half, angle, alpha=255):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = (90, 150, 255, alpha)
    pts = []
    for dx, dy in ((-half, -half), (half, -half), (half, half), (-half, half)):
        a = math.radians(angle)
        rx = dx * math.cos(a) - dy * math.sin(a)
        ry = dx * math.sin(a) + dy * math.cos(a)
        pts.append((cx + rx, cy + ry))
    d.polygon(pts, outline=col, width=3)
    for px, py in pts:
        d.rectangle([px - 5, py - 5, px + 5, py + 5], fill=(255, 255, 255, 255), outline=col, width=2)
    img.alpha_composite(layer)


def main():
    photo = load(os.path.join(HERE, '..', '素材箱', '_DSC9970_Portra_400_Portra_Endura.png'))
    x0, y0, x1, y1 = find_photo_rect(photo)
    ix, iy = int((x1 - x0) * 0.04), int((y1 - y0) * 0.04)
    photo = photo.crop((x0 + ix, y0 + iy, x1 - ix, y1 - iy))
    pw, ph = photo.size
    m = min(pw, ph)
    photo = photo.crop(((pw - m) // 2, (ph - m) // 2, (pw - m) // 2 + m, (ph - m) // 2 + m))
    card = rounded(photo.resize((CARD, CARD), Image.LANCZOS), 26)

    shadow = Image.new('RGBA', (CARD + 60, CARD + 60), (0, 0, 0, 0))
    sh = Image.new('RGBA', (CARD, CARD), (0, 0, 0, 150))
    sh = rounded(sh, 26).filter(ImageFilter.GaussianBlur(18))
    shadow.alpha_composite(sh, (30, 34))

    cat = emoji('😻', 150)
    title_f = font('segoeuib.ttf', 54)
    sub_f = font('msyhbd.ttc', 24)
    hint_f = font('msyh.ttc', 20)

    frames = []
    total_hold = 6

    # 阶段 1：下落 0..9
    for i in range(9):
        t = i / 8
        e = ease_out_back(t)
        img = bg_image()
        img.alpha_composite(shadow, (CARD_X - 30, CARD_Y - 30))
        img.alpha_composite(card, (CARD_X, CARD_Y))

        cx = CARD_X + CARD / 2
        cy = CARD_Y + CARD / 2
        sy = cy - (1 - e) * 150
        st = cat.rotate(-12 * (1 - e), expand=True, resample=Image.BICUBIC)
        img.alpha_composite(st, (int(cx - st.width / 2), int(sy - st.height / 2)))

        d = ImageDraw.Draw(img)
        d.text((CARD_X + CARD + 48, 120), 'Paji', font=title_f, fill=(255, 255, 255, 255))
        d.text((CARD_X + CARD + 50, 190), '贴 emoji', font=sub_f, fill=(190, 200, 240, 255))
        draw_cursor(d, cx + 40, sy - 20)
        frames.append(img.convert('RGB'))

    # 阶段 2：变换框 + 旋转 10..26
    for i in range(15):
        t = i / 14
        ang = ease_in_out(t) * 26
        img = bg_image()
        img.alpha_composite(shadow, (CARD_X - 30, CARD_Y - 30))
        img.alpha_composite(card, (CARD_X, CARD_Y))
        cx = CARD_X + CARD / 2
        cy = CARD_Y + CARD / 2
        st = cat.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))
        sel_box(img, cx, cy, cat.width / 2 + 8, ang, alpha=int(120 + 100 * t))
        d = ImageDraw.Draw(img)
        d.text((CARD_X + CARD + 48, 120), 'Paji', font=title_f, fill=(255, 255, 255, 255))
        d.text((CARD_X + CARD + 50, 190), '拖动 / 缩放 / 旋转', font=sub_f, fill=(190, 200, 240, 255))
        hx = cx + math.cos(math.radians(ang - 90)) * (cat.width / 2 + 40)
        hy = cy + math.sin(math.radians(ang - 90)) * (cat.width / 2 + 40)
        draw_cursor(d, hx, hy)
        frames.append(img.convert('RGB'))

    # 阶段 3：导出提示
    for i in range(total_hold):
        img = bg_image()
        img.alpha_composite(shadow, (CARD_X - 30, CARD_Y - 30))
        img.alpha_composite(card, (CARD_X, CARD_Y))
        cx, cy = CARD_X + CARD / 2, CARD_Y + CARD / 2
        st = cat.rotate(26, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))
        d = ImageDraw.Draw(img)
        d.text((CARD_X + CARD + 48, 120), 'Paji', font=title_f, fill=(255, 255, 255, 255))
        d.text((CARD_X + CARD + 50, 190), '导出原图分辨率', font=sub_f, fill=(190, 200, 240, 255))
        # 完成勾
        bx, by = CARD_X + CARD + 50, 250
        d.rounded_rectangle([bx, by, bx + 176, by + 46], radius=12, fill=(46, 160, 96, 255))
        d.text((bx + 24, by + 10), '✓ 已导出', font=sub_f, fill=(255, 255, 255, 255))
        frames.append(img.convert('RGB'))

    out = os.path.join(HERE, 'docs', 'demo.gif')
    small = [f.resize((720, 458), Image.LANCZOS).quantize(colors=128, method=Image.MEDIANCUT)
             for f in frames]
    small[0].save(out, save_all=True, append_images=small[1:],
                  duration=int(1000 / FPS), loop=0, optimize=True, disposal=2)
    print('demo.gif', os.path.getsize(out) // 1024, 'KB,', len(frames), 'frames')


if __name__ == '__main__':
    main()
