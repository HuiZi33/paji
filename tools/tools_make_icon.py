# -*- coding: utf-8 -*-
"""生成 Paji 图标：使用 Noto Color Emoji 的 😻（U+1F63B，SIL OFL 1.1）。

产物：
    icon.ico           多尺寸 Windows 图标（256/128/64/48/32/16）
    icon_preview.png   各尺寸并排预览
"""
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PIL import Image

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
SRC = os.path.join(HERE, 'assets', 'noto', 'emoji_u1f63b.png')
SIZES = [256, 128, 64, 48, 32, 16]
MARGIN = 0.04          # 四周留白比例


def build_master():
    im = Image.open(SRC).convert('RGBA')
    box = im.getbbox()
    if box:
        im = im.crop(box)                        # 去掉透明边
    side = max(im.width, im.height)
    pad = int(side * MARGIN * 2)
    canvas = Image.new('RGBA', (side + pad, side + pad), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((canvas.width - im.width) // 2,
                               (canvas.height - im.height) // 2))
    return canvas


def main():
    master = build_master().resize((1024, 1024), Image.LANCZOS)
    ico = os.path.join(HERE, 'icon.ico')
    master.save(ico, sizes=[(s, s) for s in SIZES])

    tiles = []
    for s in SIZES:
        t = master.resize((s, s), Image.LANCZOS)
        bg = Image.new('RGBA', (s, s), (30, 32, 38, 255))
        bg.alpha_composite(t)
        tiles.append(bg.resize((128, 128), Image.NEAREST))
    sheet = Image.new('RGB', (128 * len(tiles) + 10 * (len(tiles) - 1), 128), (24, 26, 32))
    for i, t in enumerate(tiles):
        sheet.paste(t.convert('RGB'), (i * 138, 0))
    sheet.save(os.path.join(HERE, 'icon_preview.png'))
    print('icon.ico', os.path.getsize(ico) // 1024, 'KB')
    print('源:', os.path.basename(SRC))


if __name__ == '__main__':
    main()
