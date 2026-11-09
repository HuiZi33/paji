# -*- coding: utf-8 -*-
"""给当前版本打一个完整源码快照（工作区内，替代 git 的轻量方案）。

用法：
    python tools_snapshot.py            # 用 paji.py 里的 VER
    python tools_snapshot.py --force    # 覆盖已存在的同名快照

产物：
    versions/<版本号>/        该版本的完整源码副本
    versions/<版本号>/manifest.json
    versions/INDEX.md         版本索引
"""
import hashlib
import json
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import re
import shutil
import time

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
VERSIONS = os.path.join(HERE, 'versions')

TRACK = [
    'paji.py', 'emoji_list.py', 'Paji.spec', 'build.cmd', 'README.md',
    'tools/compat_test.py', 'tools/test_degraded.py',
    'tools/tools_archive.py', 'tools/tools_build_emoji_list.py',
    'tools/tools_fetch_emoji.py', 'tools/tools_build_thumbs.py',
    'tools/tools_make_icon.py', 'tools/tools_make_intro.py',
    'tools/tools_check_exe.py', 'tools/tools_snapshot.py',
    'flag_codes.json', 'emoji_names.json', 'icon.ico',
]


def current_ver():
    t = open(os.path.join(HERE, 'paji.py'), encoding='utf-8').read()
    m = re.search(r"^VER\s*=\s*'([^']+)'", t, re.M)
    return m.group(1) if m else 'unknown'


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def snapshot(ver, force=False):
    dest = os.path.join(VERSIONS, ver)
    if os.path.isdir(dest) and not force:
        print(f'快照已存在：versions\\{ver}\\（用 --force 覆盖）')
        return 0
    os.makedirs(dest, exist_ok=True)
    manifest = {'version': ver, 'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'files': {}}
    n = 0
    for name in TRACK:
        src = os.path.join(HERE, name)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dest, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        manifest['files'][name] = {'size': os.path.getsize(src), 'sha1': sha1(src)}
        n += 1
    with open(os.path.join(dest, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f'已快照 {ver}：{n} 个文件 -> versions\\{ver}\\')
    write_index()
    return 0


def write_index():
    os.makedirs(VERSIONS, exist_ok=True)
    rows = []
    for name in sorted(os.listdir(VERSIONS)):
        d = os.path.join(VERSIONS, name)
        if not os.path.isdir(d):
            continue
        mf = os.path.join(d, 'manifest.json')
        when, cnt, size = '-', 0, 0
        if os.path.exists(mf):
            m = json.load(open(mf, encoding='utf-8'))
            when = m.get('created', '-')
            cnt = len(m.get('files', {}))
            size = sum(v['size'] for v in m.get('files', {}).values())
        rows.append((name, when, cnt, size))
    lines = ['# Paji 版本快照', '',
             '> 每个版本的完整源码副本，只增不减。', '',
             '| 版本 | 时间 | 文件数 | 大小 |', '|---|---|---|---|']
    for name, when, cnt, size in rows:
        lines.append(f'| {name} | {when} | {cnt} | {size / 1024:.0f} KB |')
    lines += ['', '生成：`python tools_snapshot.py`', '']
    open(os.path.join(VERSIONS, 'INDEX.md'), 'w', encoding='utf-8').write('\n'.join(lines))


def main():
    import sys
    force = '--force' in sys.argv
    return snapshot(current_ver(), force)


if __name__ == '__main__':
    raise SystemExit(main())
