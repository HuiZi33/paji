# -*- coding: utf-8 -*-
"""下载 Paji 的 emoji 资源（Google Noto）。

用法：
    python tools_fetch_emoji.py            # 下载/补齐
    python tools_fetch_emoji.py --verify   # 只校验

表情包（assets/meme/）由用户自己放 PNG，脚本不碰。
资源会被 --add-data "assets;assets" 打进 exe。
"""
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import sys
import time
import urllib.request

from emoji_list import EMOJIS

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
ASSETS = os.path.join(HERE, 'assets')
NOTO = 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/512/emoji_u{c}.png'
FLAGS = 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/third_party/region-flags/png/{code}.png'

SKIP = {0xFE0F, 0xFE0E}


def cps(ch):
    return [ord(c) for c in ch if ord(c) not in SKIP]


def noto_name(ch):
    # Noto 的文件名是 4 位起的小写十六进制：0023 / 1f600
    return 'emoji_u' + '_'.join('%04x' % x for x in cps(ch)) + '.png'


def is_png(path):
    try:
        with open(path, 'rb') as f:
            return f.read(8) == b'\x89PNG\r\n\x1a\n'
    except OSError:
        return False


def fetch(url, dst, retries=2):
    if is_png(dst):
        return 'cached'
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            if not data.startswith(b'\x89PNG'):
                return 'not-found'
            with open(dst, 'wb') as f:
                f.write(data)
            return 'ok'
        except Exception:
            if attempt == retries:
                return 'fail'
            time.sleep(1)


def fetch_flag(code, dst, retries=2):
    """国旗：有些是符号链接（内容形如 `NO.p`），需要跟随到真图。"""
    if is_png(dst):
        return 'cached'
    for attempt in range(retries + 1):
        try:
            data = _get(FLAGS.format(code=code))
            if data.startswith(b'\x89PNG'):
                with open(dst, 'wb') as f:
                    f.write(data)
                return 'ok'
            # 跟随符号链接目标
            text = data.strip().decode('ascii', 'ignore')
            if len(text) >= 2 and text[:2].isalpha():
                target = text[:2].upper()
                data2 = _get(FLAGS.format(code=target))
                if data2.startswith(b'\x89PNG'):
                    with open(dst, 'wb') as f:
                        f.write(data2)
                    return 'linked:' + target
            return 'not-found'
        except Exception:
            if attempt == retries:
                return 'fail'
            time.sleep(1)


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download():
    d = os.path.join(ASSETS, 'noto')
    os.makedirs(d, exist_ok=True)
    stat = {'ok': 0, 'cached': 0, 'missing': 0, 'failed': 0, 'not-found': 0}
    for ch in EMOJIS:
        nm = noto_name(ch)
        cps = [ord(c) for c in ch]
        dst = os.path.join(d, nm)
        if len(cps) == 2 and all(0x1F1E6 <= c <= 0x1F1FF for c in cps):
            code = ''.join(chr(ord('A') + c - 0x1F1E6) for c in cps)
            r = fetch_flag(code, dst)
        else:
            r = fetch(NOTO.format(c=nm[7:-4]), dst)
        stat[r if r in stat else 'not-found'] += 1
    print(f'noto       new={stat["ok"]:3d} cached={stat["cached"]:3d} '
          f'missing={stat["missing"]:3d} failed={stat["failed"]:3d}')
    meme = os.path.join(ASSETS, 'meme')
    if os.path.isdir(meme):
        print('meme       ', ', '.join(sorted(os.listdir(meme))) or '(empty)')
    print('done')
    return 0


def verify():
    bad = 0
    d = os.path.join(ASSETS, 'noto')
    n = 0
    if os.path.isdir(d):
        for f in os.listdir(d):
            if is_png(os.path.join(d, f)):
                n += 1
            else:
                bad += 1
    print(f'noto       valid={n}')
    dm = os.path.join(ASSETS, 'meme')
    if os.path.isdir(dm):
        for f in sorted(os.listdir(dm)):
            if not is_png(os.path.join(dm, f)):
                bad += 1
            print(f'meme/{f}')
    print('invalid files:', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(verify() if '--verify' in sys.argv else download())
