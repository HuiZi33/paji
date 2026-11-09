# -*- coding: utf-8 -*-
"""生成缩略图图集：把 900 个 emoji 缩到 64px 拼成一张大图。

目的：运行时只解码 1 张图，切分类/换主题时直接从图集裁切，
      不再逐个打开 512px PNG（这是卡顿的主因）。

产物：
  assets/thumb_atlas.png   图集
  assets/thumb_index.json  {字符 或 '__meme__': [x, y, w, h]}
"""
import json
import os

from PIL import Image

from emoji_list import EMOJIS

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'assets')
CELL = 64
COLS = 32


def fit_square(img, size):
    """等比缩放到 size 内，居中放进透明方块（旗帜不会被拉变形）。"""
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    im = img.copy()
    im.thumbnail((size, size), Image.LANCZOS)
    canvas.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
    return canvas


def load(path):
    return Image.open(path).convert('RGBA')


def main():
    items = []
    # 表情包优先（放第一个）
    meme = os.path.join(ASSETS, 'meme', 'epicface.png')
    if os.path.exists(meme):
        items.append(('__meme__', meme))

    missing = 0
    for ch in EMOJIS:
        cps = [ord(c) for c in ch if ord(c) not in (0xFE0F, 0xFE0E)]
        name = 'emoji_u' + '_'.join('%04x' % c for c in cps) + '.png'
        p = os.path.join(ASSETS, 'noto', name)
        if os.path.exists(p):
            items.append((ch, p))
        else:
            missing += 1

    rows = (len(items) + COLS - 1) // COLS
    atlas = Image.new('RGBA', (COLS * CELL, rows * CELL), (0, 0, 0, 0))
    index = {}
    for i, (key, path) in enumerate(items):
        col, row = i % COLS, i // COLS
        try:
            thumb = fit_square(load(path), CELL)
        except Exception:
            continue
        atlas.alpha_composite(thumb, (col * CELL, row * CELL))
        index[key] = [col * CELL, row * CELL, CELL, CELL]

    out_png = os.path.join(ASSETS, 'thumb_atlas.png')
    out_json = os.path.join(ASSETS, 'thumb_index.json')
    atlas.save(out_png, optimize=True)
    json.dump(index, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False)

    print(f'items {len(items)}  missing {missing}')
    print(f'atlas {atlas.width}x{atlas.height}  {os.path.getsize(out_png)/1024:.0f} KB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
