# -*- coding: utf-8 -*-
"""从 emoji_names.json 生成 emoji_list.py（按类别优先，控制总量）。

用法：python tools_build_emoji_list.py
输出：emoji_list.py（覆盖）
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = os.path.join(HERE, 'emoji_names.json')
OUT = os.path.join(HERE, 'emoji_list.py')

SKIP = {0xFE0F, 0xFE0E}
SKIN = set(range(0x1F3FB, 0x1F400))

# (名称, [codepoint 区间]) —— 顺序即优先级
CATEGORIES = [
    ('flags',     [(0x1F1E6, 0x1F1FF)]),
    ('faces',     [(0x1F600, 0x1F64F), (0x1F910, 0x1F92F), (0x1F970, 0x1F976), (0x1F97A, 0x1F97A)]),
    ('people',    [(0x1F440, 0x1F4FF), (0x1F900, 0x1F90F), (0x1F930, 0x1F93F), (0x1F977, 0x1F9AF),
                   (0x1F466, 0x1F469), (0x1F47A, 0x1F47F), (0x1F480, 0x1F483)]),
    ('animals',   [(0x1F400, 0x1F43E), (0x1F980, 0x1F98F), (0x1F990, 0x1F9AF)]),
    ('nature',    [(0x1F300, 0x1F32C), (0x1F330, 0x1F343), (0x1F344, 0x1F344)]),
    ('food',      [(0x1F32D, 0x1F37F), (0x1F950, 0x1F96F), (0x1F9C0, 0x1F9CB)]),
    ('travel',    [(0x1F680, 0x1F6FF), (0x1F30D, 0x1F320)]),
    ('activity',  [(0x1F380, 0x1F3D3)]),
    ('objects',   [(0x1F4A0, 0x1F4FF), (0x1F500, 0x1F5FF), (0x1F9E0, 0x1F9FF)]),
    ('symbols',   [(0x2600, 0x27BF), (0x2B00, 0x2BFF), (0x1F000, 0x1F02F), (0x2049, 0x2049)]),
]


def parse(name):
    body = name[len('emoji_u'):-len('.png')]
    try:
        cps = [int(x, 16) for x in body.split('_')]
    except ValueError:
        return None
    if any(c in SKIP for c in cps):
        cps = [c for c in cps if c not in SKIP]
    if not cps:
        return None
    if any(c in SKIN for c in cps):
        return None
    # 区域指示符：只保留成对（= 国旗），单个的丢弃
    regional = [c for c in cps if 0x1F1E6 <= c <= 0x1F1FF]
    if regional:
        if len(cps) == 2 and len(regional) == 2:
            return cps
        return None
    if len(cps) > 2:
        # 允许「白旗 + ZWJ + 符号」的旗帜序列（彩虹 🌈 / 跨性别 ⚧ 等）
        if len(cps) >= 3 and cps[0] == 0x1F3F3 and 0x200D in cps:
            return cps
        return None
    return cps


def category_of(cps):
    if cps and cps[0] == 0x1F3F3:
        return 0        # 彩虹 / 跨性别等 ZWJ 旗帜，归到 flags
    for i, (_, ranges) in enumerate(CATEGORIES):
        for lo, hi in ranges:
            if all(lo <= c <= hi for c in cps):
                return i
    return None


def main():
    if not os.path.exists(NAMES):
        print('missing emoji_names.json')
        return 1
    names = json.load(open(NAMES, encoding='utf-8'))
    buckets = {i: [] for i in range(len(CATEGORIES))}
    seen = set()
    for n in names:
        cps = parse(n)
        if not cps:
            continue
        cat = category_of(cps)
        if cat is None:
            continue
        key = tuple(cps)
        if key in seen:
            continue
        seen.add(key)
        buckets[cat].append((cps, n))

    picked = []
    # 国旗：Noto 的 512 目录里没有，用 region-flags 的国家代码反推成 emoji
    flag_file = os.path.join(HERE, 'flag_codes.json')
    flags = []
    if os.path.exists(flag_file):
        for code in json.load(open(flag_file, encoding='utf-8')):
            cps = [0x1F1E6 + ord(c) - ord('A') for c in code.upper()]
            flags.append((cps, 'flag_' + code))
    buckets[0] = flags + buckets[0]     # 国旗 + 彩虹/跨性别等 ZWJ 旗帜

    # 每类配额（避免按顺序截断把后面的分类饿死）
    QUOTA = {
        'flags': 10 ** 9,
        'faces': 150,
        'people': 120,
        'animals': 80,
        'nature': 70,
        'food': 80,
        'travel': 70,
        'activity': 70,
        'objects': 80,
        'symbols': 80,
    }
    for i, (name, _) in enumerate(CATEGORIES):
        quota = QUOTA.get(name, 50)
        for cps, n in sorted(buckets[i])[:quota]:
            picked.append(''.join(chr(c) for c in cps))

    rows = []
    row = ''
    for ch in picked:
        row += ch + ' '
        if len(row) >= 100:
            rows.append(row)
            row = ''
    if row.strip():
        rows.append(row if row.endswith(' ') else row + ' ')

    body = ''.join('    ' + repr(r) + '\n' for r in rows)
    text = ('# -*- coding: utf-8 -*-\n'
            '"""Paji 的 emoji 清单（由 tools_build_emoji_list.py 生成）。"""\n\n'
            'EMOJIS = (\n' + body + ').split()\n')
    open(OUT, 'w', encoding='utf-8').write(text)

    counts = {}
    for i, (label, _) in enumerate(CATEGORIES):
        counts[label] = len(buckets[i])
    print('picked', len(picked), 'of', sum(counts.values()))
    print('by category:', counts)
    return 0


if __name__ == '__main__':
    sys.exit(main())
