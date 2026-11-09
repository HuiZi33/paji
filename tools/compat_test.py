# -*- coding: utf-8 -*-
"""Paji 兼容性测试（无窗口）。

覆盖：OS/DPI/字体/注册表/资源/合成/导出/主题/字号/特殊路径。
用法：python compat_test.py [--verbose]
退出码 0 = 全部通过。
"""
import os
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import sys
import json
import shutil
import tempfile
import time

HERE = _ROOT  # 项目根目录（脚本已移入 tools/）
sys.path.insert(0, HERE)

RESULTS = []


def check(name, fn):
    t0 = time.time()
    try:
        detail = fn()
        ok = True
    except Exception as e:
        detail = f'{type(e).__name__}: {e}'
        ok = False
    ms = int((time.time() - t0) * 1000)
    RESULTS.append((ok, name, detail, ms))
    print(('  [PASS] ' if ok else '  [FAIL] ') + f'{name}  ({ms} ms)')
    if detail:
        print(f'         {detail}')
    return ok


def main():
    print('=' * 68)
    print('Paji 兼容性测试')
    print('=' * 68)

    import platform
    print(f'  OS: {platform.system()} {platform.release()} {platform.version()}')
    print(f'  Python: {sys.version.split()[0]}  ({platform.machine()})')
    print()

    import paji
    from PIL import Image

    # --- 1. 运行环境
    check('DPI 感知可设置', lambda: (paji.enable_dpi_awareness(), 'SetProcessDpiAwareness(2) ok')[1])

    import tkinter as tk
    root = tk.Tk()
    root.withdraw()

    def tk_info():
        return f'Tk {root.tk.call("info", "patchlevel")} / Tcl {root.tk.call("info", "tclversion")}'
    check('Tk 可用', tk_info)

    def dpi_info():
        dpi = root.winfo_fpixels('1i')
        return f'{dpi:.0f} DPI ≈ {dpi / 96 * 100:.0f}%'
    check('读取系统 DPI', dpi_info)

    # --- 2. 字体
    for name, path in (('Segoe UI Emoji', paji.FONT_PATH),
                       ('微软雅黑', os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'msyh.ttc'))):
        check(f'字体存在：{name}', lambda p=path: p)

    # --- 3. 注册表（主题）
    def reg():
        v = paji.system_theme()
        assert v in ('light', 'dark')
        return f'AppsUseLightTheme → {v}'
    check('读取系统主题', reg)

    # --- 4. 资源
    def assets():
        count = 0
        bad = 0
        d = os.path.join(paji.ASSETS, 'noto')
        for f in os.listdir(d):
            p = os.path.join(d, f)
            try:
                with Image.open(p) as im:
                    im.verify()
                count += 1
            except Exception:
                bad += 1
        assert bad == 0, f'{bad} 个损坏'
        return f'noto {count} 个，0 损坏'
    check('emoji 资源完整', assets)

    def atlas():
        p = os.path.join(paji.ASSETS, 'thumb_atlas.png')
        if not os.path.exists(p):
            raise FileNotFoundError('缺少缩略图图集')
        return f'{os.path.getsize(p) / 1048576:.1f} MB'
    check('缩略图图集存在', atlas)

    # --- 5. 界面构建
    app = paji.App(root)
    root.update()

    def build_ui():
        return f'列数 {app._grid_cols()}，缩放 {app.ui:.2f}×，字号 {int(app.font_scale * 100)}%'
    check('界面构建', build_ui)

    # --- 6. 合成与导出
    tmp = tempfile.mkdtemp(prefix='paji_compat_')

    def make_base():
        im = Image.new('RGBA', (800, 600), (40, 60, 90, 255))
        return im

    def compose():
        app.base = make_base()
        app.base_path = os.path.join(tmp, 'base.png')
        app.stickers = []
        app.add_emoji('😻')
        app.add_emoji('🇨🇳')
        assert len(app.stickers) == 2
        out = app.render_full()
        assert out.size == (800, 600)
        p = os.path.join(tmp, 'out.png')
        out.save(p)
        assert os.path.getsize(p) > 2000
        return f'2 贴纸 → {os.path.getsize(p)} bytes'
    check('合成 + 导出 PNG', compose)

    def export_jpg():
        p = os.path.join(tmp, 'out.jpg')
        app.render_full().convert('RGB').save(p, quality=95)
        assert os.path.getsize(p) > 2000
        return f'{os.path.getsize(p)} bytes'
    check('导出 JPG', export_jpg)

    # --- 7. 主题
    def themes():
        seen = []
        for _ in range(3):
            app.cycle_theme()
            seen.append(app.theme_mode)
        assert set(seen) == {'dark', 'light', 'system'}, seen
        cfg = json.load(open(paji.config_path(), encoding='utf-8'))
        assert cfg.get('theme') == app.theme_mode
        return ' → '.join(seen)
    check('主题三态切换', themes)

    # --- 8. 字号
    def font_scale():
        before = app.font_scale
        app.change_font(0.1)
        up = app.font_scale
        app.change_font(-0.1)
        assert up > before and abs(app.font_scale - before) < 0.001
        return f'{int(before * 100)}% → {int(up * 100)}% → {int(app.font_scale * 100)}%'
    check('字号调节', font_scale)

    # --- 9. 特殊路径
    def weird_paths():
        cases = ['空格 目录', "带'撇号", 'Ünïcødé', '中文目录']
        done = []
        for c in cases:
            d = os.path.join(tmp, c)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, '照片 1.png')
            make_base().save(p)
            assert os.path.exists(p)
            done.append(c)
        return '、'.join(done)
    check('特殊路径读写', weird_paths)

    # --- 10. 配置持久化
    def config_io():
        p = paji.config_path()
        assert os.path.exists(p)
        d = json.load(open(p, encoding='utf-8'))
        assert 'font_scale' in d and 'theme' in d
        return p
    check('配置读写', config_io)

    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)

    ok = sum(1 for r in RESULTS if r[0])
    total = len(RESULTS)
    print()
    print('=' * 68)
    print(f'结果：{ok}/{total} 通过')
    if ok < total:
        print('失败项：')
        for good, name, detail, _ in RESULTS:
            if not good:
                print(f'  - {name}: {detail}')
    print('=' * 68)
    return 0 if ok == total else 1


if __name__ == '__main__':
    sys.exit(main())
