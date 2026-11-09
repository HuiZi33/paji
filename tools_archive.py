# -*- coding: utf-8 -*-
"""把 dist 里的成品归档到 releases/（同名不覆盖，保证每个旧版本都留档）。"""
import hashlib
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, 'dist')
REL = os.path.join(HERE, 'releases')


def sha1(path, limit=1 << 20):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        h.update(f.read(limit))
    return h.hexdigest()[:12]


def main():
    os.makedirs(REL, exist_ok=True)
    if not os.path.isdir(DIST):
        print('没有 dist 目录')
        return 1
    archived, skipped = [], []
    for name in sorted(os.listdir(DIST)):
        if not name.lower().endswith('.exe'):
            continue
        src = os.path.join(DIST, name)
        dst = os.path.join(REL, name)
        if os.path.exists(dst):
            skipped.append(name)
            continue
        shutil.copy2(src, dst)
        archived.append(name)

    for n in archived:
        p = os.path.join(REL, n)
        print(f'归档 {n}  {os.path.getsize(p) / 1048576:.1f} MB  sha1:{sha1(p)}')
    for n in skipped:
        print(f'已存在，跳过 {n}')
    if not archived and not skipped:
        print('dist 里没有 exe')
    print(f'\nreleases 现有 {len([f for f in os.listdir(REL) if f.lower().endswith(".exe")])} 个版本')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
