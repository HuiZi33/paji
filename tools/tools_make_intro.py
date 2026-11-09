# -*- coding: utf-8 -*-
"""生成 Paji 的宣传图（preview.png，README 顶部使用）。"""
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

cats, _ = paji.build_catalog()

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
ASSETS = os.path.join(HERE, 'assets')
FONTS = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
W, H = 1920, 1080


def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), size)
    except Exception:
        return ImageFont.load_default()


def load(path):
    return Image.open(path).convert('RGBA')


def emoji(ch, size):
    import paji
    return paji.render_emoji('noto', ch, size)


def rounded(img, radius):
    """圆角遮罩：与已有 alpha 相乘，保留透明区域（旋转后的透明角不会变黑）。"""
    from PIL import ImageChops
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1],
                                           radius=radius, fill=255)
    out = img.copy()
    out.putalpha(ImageChops.multiply(out.split()[3], mask))
    return out


def find_photo_rect(im, thresh=45, limit=0.5):
    """找出胶片框内真正的照片矩形（去掉黑边/齿孔）。

    做法：按行/列统计"亮像素占比"，取最长的连续高亮区间。
    """
    g = im.convert('L')
    w, h = g.size
    px = g.load()
    sx = max(1, w // 400)
    sy = max(1, h // 400)

    rows = []
    for y in range(0, h, sy):
        tot = n = 0
        for x in range(0, w, sx):
            n += 1
            if px[x, y] > thresh:
                tot += 1
        rows.append(tot / max(1, n))

    cols = []
    for x in range(0, w, sx):
        tot = n = 0
        for y in range(0, h, sy):
            n += 1
            if px[x, y] > thresh:
                tot += 1
        cols.append(tot / max(1, n))

    def longest(fs):
        best = (0, 0)
        start = None
        for i, f in enumerate(fs):
            if f >= limit:
                if start is None:
                    start = i
                if i - start > best[1] - best[0]:
                    best = (start, i)
            else:
                start = None
        return best

    r0, r1 = longest(rows)
    c0, c1 = longest(cols)
    return (c0 * sx, r0 * sy, min(w, (c1 + 1) * sx), min(h, (r1 + 1) * sy))


def main():
    # 背景渐变
    bg = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(24 + 40 * t), int(22 + 18 * t), int(52 + 70 * t)))
    img = bg.convert('RGBA')

    # 左侧照片（圆角 + 阴影）
    photo = load(os.path.join(HERE, '..', '素材箱', '_DSC9970_Portra_400_Portra_Endura.png'))
    side = 780
    # 自动识别"真正的照片区域"，去掉胶片黑边（不再靠手调比例）
    x0, y0, x1, y1 = find_photo_rect(photo)
    inset_x = int((x1 - x0) * 0.04)
    inset_y = int((y1 - y0) * 0.04)
    photo = photo.crop((x0 + inset_x, y0 + inset_y, x1 - inset_x, y1 - inset_y))
    pw, ph = photo.size
    m = min(pw, ph)
    cx0 = (pw - m) // 2
    cy0 = (ph - m) // 2
    photo = photo.crop((cx0, cy0, cx0 + m, cy0 + m))
    photo = photo.resize((side, side), Image.LANCZOS)
    photo = rounded(photo, 32)

    # 往照片上贴东西
    stickers = [
        (emoji('😻', 140), (0.16, 0.18)),
        (emoji('🎉', 120), (0.78, 0.16)),
        (emoji('😎', 150), (0.78, 0.74)),
        (emoji('🌈', 110), (0.18, 0.76)),
    ]
    for st, (px, py) in stickers:
        photo.alpha_composite(st, (int(side * px - st.width / 2), int(side * py - st.height / 2)))

    shadow = Image.new('RGBA', (side + 80, side + 80), (0, 0, 0, 0))
    sh = Image.new('RGBA', (side, side), (0, 0, 0, 150))
    sh = rounded(sh, 32).filter(ImageFilter.GaussianBlur(26))
    shadow.alpha_composite(sh, (40, 46))
    img.alpha_composite(shadow, (70, 120))
    img.alpha_composite(photo, (110, 160))

    # 右侧文字（与照片留出安全间距，避免重叠）
    d = ImageDraw.Draw(img)
    x = 1030
    d.line([(x - 60, 200), (x - 60, 900)], fill=(90, 100, 150, 255), width=2)
    d.text((x, 128), 'Paji', font=font('segoeuib.ttf', 180), fill=(255, 255, 255, 255))
    d.text((x + 6, 420), '啪叽 · 表情工坊', font=font('msyhbd.ttc', 54), fill=(196, 210, 255, 255))
    # 不显示版本号：宣传图可以长期复用

    lines = [
        '导入照片 · 贴 emoji · 旋转缩放',
        f'{len(EMOJIS)} 个 Noto emoji · {len(cats)} 个分类',
        '单文件 exe · 绿色免安装',
    ]
    y = 595
    for ln in lines:
        d.text((x + 8, y), ln, font=font('msyh.ttc', 34), fill=(215, 222, 240, 255))
        y += 56

    # 底部 emoji 条
    row = ['😀', '😻', '🥺', '🎉', '🌈', '🏳\u200d⚧', '🍕', '🐼']
    ex = x + 4
    for ch in row:
        e = emoji(ch, 58)
        img.alpha_composite(e, (ex, 795))
        ex += 74

    out = os.path.join(HERE, 'docs', 'preview.png')
    img.convert('RGB').save(out, quality=95)
    print('intro written', out, os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
