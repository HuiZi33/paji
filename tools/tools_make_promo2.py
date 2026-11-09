# -*- coding: utf-8 -*-
"""生成第二版宣传图（intro2.png）：倾斜卡片 + 特性胶囊。"""
import math
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import paji
from emoji_list import EMOJIS
from tools_make_intro import find_photo_rect, emoji, font, load, rounded

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
ASSETS = os.path.join(HERE, 'assets')
W, H = 1920, 1080
cats, _ = paji.build_catalog()


def gradient_bg():
    bg = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(18 + 26 * t), int(20 + 16 * t), int(38 + 46 * t)))
    # 右侧淡紫辉光
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.45, -H * 0.3, W * 1.2, H * 1.1], fill=(46, 34, 86))
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    return Image.blend(bg, glow, 0.55).convert('RGBA')


def tilted(img, angle, size):
    """裁成正方形、缩放、旋转（含透明边）。"""
    pw, ph = img.size
    m = min(pw, ph)
    img = img.crop(((pw - m) // 2, (ph - m) // 2, (pw - m) // 2 + m, (ph - m) // 2 + m))
    img = img.resize(size, Image.LANCZOS)
    return img.rotate(angle, expand=True, resample=Image.BICUBIC)


def shadow_of(card, blur=26, alpha=150, offset=(16, 24)):
    """用卡片自己的 alpha 生成投影，返回 (图像, 相对卡片的放置偏移)。"""
    a = card.split()[3].point(lambda v: int(v * alpha / 255))
    sh = Image.new('RGBA', card.size, (0, 0, 0, 255))
    sh.putalpha(a)
    pad = blur * 2
    big = Image.new('RGBA', (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    big.alpha_composite(sh, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    return big, (offset[0] - pad, offset[1] - pad)


def main():
    img = gradient_bg()

    photo = load(os.path.join(HERE, '..', '素材箱', '_DSC9970_Portra_400_Portra_Endura.png'))
    x0, y0, x1, y1 = find_photo_rect(photo)
    ix, iy = int((x1 - x0) * 0.04), int((y1 - y0) * 0.04)
    photo = photo.crop((x0 + ix, y0 + iy, x1 - ix, y1 - iy))

    card = 760
    # 单张卡片 + 柔和投影
    front = tilted(photo, -4.5, (card, card))
    front = rounded(front, 34)
    for st, (px, py) in [
        (emoji('😻', 150), (0.17, 0.19)),
        (emoji('🎉', 126), (0.80, 0.17)),
        (emoji('😎', 150), (0.80, 0.76)),
        (emoji('🌈', 116), (0.19, 0.78)),
    ]:
        front.alpha_composite(st, (int(card * px - st.width / 2), int(card * py - st.height / 2)))

    fx, fy = 110, 150
    sh, off = shadow_of(front, blur=46, alpha=95, offset=(12, 20))
    img.alpha_composite(sh, (fx + off[0], fy + off[1]))
    img.alpha_composite(front, (fx, fy))

    d = ImageDraw.Draw(img)
    x = 1020

    # 标题
    d.text((x, 250), 'Paji', font=font('segoeuib.ttf', 176), fill=(255, 255, 255, 255))
    d.text((x + 4, 470), '啪叽 · 表情工坊', font=font('msyhbd.ttc', 52), fill=(198, 206, 255, 255))

    # 版本胶囊
    ver = f'v{paji.VER}'
    vb = d.textbbox((0, 0), ver, font=font('segoeui.ttf', 26))
    vw, vh = vb[2] - vb[0], vb[3] - vb[1]
    px0, py0 = x + 4, 556
    d.rounded_rectangle([px0, py0, px0 + vw + 34, py0 + vh + 20], radius=16,
                        fill=(64, 76, 150, 210))
    d.text((px0 + 17 - vb[0], py0 + 10 - vb[1]), ver, font=font('segoeui.ttf', 26),
           fill=(226, 232, 255, 255))

    # 特性胶囊
    chips = ['新建空白画布', f'{len(EMOJIS)} 个 emoji', '6 种导出格式']
    cy = 640
    for label in chips:
        f = font('msyh.ttc', 30)
        bb = d.textbbox((0, 0), label, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        d.rounded_rectangle([x + 4, cy, x + 4 + tw + 44, cy + th + 26], radius=18,
                            outline=(120, 132, 190, 220), width=2)
        d.text((x + 26 - bb[0], cy + 13 - bb[1]), label, font=f, fill=(214, 220, 245, 255))
        cy += th + 26 + 18

    # 底部 emoji 带
    row = ['😀', '😻', '🥺', '🎉', '🌈', '🏳\u200d⚧', '🍕', '🐼']
    ex = x + 2
    for ch in row:
        e = emoji(ch, 56)
        img.alpha_composite(e, (ex, 880))
        ex += 72

    out = os.path.join(HERE, 'intro2.png')
    img.convert('RGB').save(out, quality=95)
    print('written', out, os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
