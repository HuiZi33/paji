# -*- coding: utf-8 -*-
"""降级测试：模拟资源缺失 / 空表情包目录，确认程序不崩。

用法：python test_degraded.py
"""
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import sys
import tempfile
import shutil

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
sys.path.insert(0, HERE)

import paji


def main():
    ok = True
    print('=' * 60)
    print('Paji 降级测试（资源缺失 / 空目录）')
    print('=' * 60)

    import tkinter as tk
    from PIL import Image

    old_assets = paji.ASSETS
    tmp = tempfile.mkdtemp(prefix='paji_degraded_')
    paji.ASSETS = tmp
    os.makedirs(os.path.join(tmp, 'noto'), exist_ok=True)
    os.makedirs(os.path.join(tmp, 'meme'), exist_ok=True)

    try:
        root = tk.Tk()
        root.withdraw()
        app = paji.App(root)
        root.update()
        print('  [PASS] 空资源目录下界面仍能构建')

        # 没有 noto 图 → 应回退系统字体，不抛异常
        img = paji.render_emoji('noto', '😻', 64)
        assert img.size[0] > 0
        print(f'  [PASS] emoji 回退系统字体（{img.size[0]}×{img.size[1]}）')

        # 空表情包目录
        assert paji.meme_files() == []
        app.build_grid()
        print('  [PASS] 空表情包目录显示提示，不崩溃')

        # 合成 + 导出
        app.base = Image.new('RGBA', (400, 300), (20, 20, 20, 255))
        app.add_emoji('🎉')
        out = app.render_full()
        p = os.path.join(tmp, 'x.png')
        out.save(p)
        assert os.path.getsize(p) > 500
        print('  [PASS] 无资源时仍可导出')

        root.destroy()
    except Exception as e:
        ok = False
        print(f'  [FAIL] {type(e).__name__}: {e}')
    finally:
        paji.ASSETS = old_assets
        shutil.rmtree(tmp, ignore_errors=True)

    print('=' * 60)
    print('结果：' + ('通过' if ok else '失败'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
