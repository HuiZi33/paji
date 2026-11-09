#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paji · 啪叽  v1.7
打开一张照片，往上贴 emoji / 表情 / PNG 贴纸，导出成图。

v1.7：
  - 分类改为顶部标签（不再用下拉菜单），只显示非空分类
  - 分类按 Unicode 区块重做；「全部」里表情在前、旗帜在后
  - 旗帜分类里跨性别旗、彩虹旗排最前
  - 工具栏改为方形图标按钮；修复画布被状态栏挤窄的布局 bug
  - 去掉状态栏的字号显示

v1.6：缩略图图集 + Canvas 绘制网格（启动 2.13s → 0.89s）
v1.5：emoji 扩量、主题三选一、字号可调
v1.4~v1.0：动态列数、图标、改名、高 DPI、初版
"""

import os
import sys
import math
import json
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw, ImageFont, ImageTk
try:
    from PIL import ImageCms
except Exception:      # 极少数打包环境缺 littlecms
    ImageCms = None

import io

from emoji_list import EMOJIS

APP = 'Paji'
VER = '1.8.6-beta'


def apply_icc(im, icc_bytes):
    """把带 ICC 配置的图（Adobe RGB / ProPhoto 等）转到 sRGB，消除色差。"""
    if ImageCms is None or not icc_bytes:
        return im
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
        dst = ImageCms.createProfile('sRGB')
        return ImageCms.profileToProfile(im, src, dst, outputMode='RGBA')
    except Exception:
        return im


def srgb_profile_bytes():
    if ImageCms is None:
        return None
    try:
        return ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    except Exception:
        return None

# ---------------------------------------------------------------- 主题

THEMES = {
    'dark': dict(bg='#17181c', panel='#1f2026', canvas='#101116', btn='#2c2e36', btn_hi='#3a3d47',
                 text='#e8eaf0', sub='#aab0c0', accent='#2d6cdf', sep='#0c0d11', tab='#262832',
                 hint='#5c6274', faint='#777d8c'),
    'light': dict(bg='#f4f5f8', panel='#ffffff', canvas='#e9ebf1', btn='#eceef4', btn_hi='#dde1ea',
                  text='#1d212a', sub='#5b6373', accent='#2d6cdf', sep='#d5d9e3', tab='#e8ebf2',
                  hint='#8b93a3', faint='#9aa1af'),
}

THEME_ICONS = {'dark': '🌙', 'light': '☀️', 'system': '🖥️'}
THEME_LABELS = {'dark': '深色', 'light': '浅色', 'system': '跟随系统'}


def system_theme():
    """读 Windows 的「应用模式」：1 = 浅色，0 = 深色。"""
    if sys.platform != 'win32':
        return 'dark'
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as k:
            v, _ = winreg.QueryValueEx(k, 'AppsUseLightTheme')
            return 'light' if v else 'dark'
    except Exception:
        return 'dark'


def resolve_theme(mode):
    return system_theme() if mode == 'system' else mode


# ---------------------------------------------------------------- 高 DPI


def enable_dpi_awareness():
    """必须在创建 Tk 之前调用，否则窗口和系统对话框都会被系统拉伸发糊。"""
    if sys.platform != 'win32':
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def asset_root():
    if getattr(sys, 'frozen', False):
        return os.path.join(getattr(sys, '_MEIPASS', '.'), 'assets')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')


ASSETS = asset_root()
FONT_PATH = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'seguiemj.ttf')

# ---------------------------------------------------------------- 配置


def config_dir():
    base = os.environ.get('APPDATA') or os.path.expanduser('~')
    d = os.path.join(base, 'Paji')
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def config_path():
    return os.path.join(config_dir(), 'config.json')


def load_config():
    try:
        with open(config_path(), encoding='utf-8') as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(config_path(), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=1)
    except Exception:
        pass


# ---------------------------------------------------------------- emoji 分类

CATEGORIES = [
    ('all', '全部'),
    ('faces', '表情'),
    ('people', '人物'),
    ('animals', '动物'),
    ('food', '食物'),
    ('travel', '旅行'),
    ('activity', '活动'),
    ('objects', '物品'),
    ('symbols', '符号'),
    ('flags', '旗帜'),
]

SKIP_CPS = {0xFE0F, 0xFE0E}


def cps_of(ch):
    return [ord(c) for c in ch if ord(c) not in SKIP_CPS]


def png_name(set_name, ch):
    cps = cps_of(ch)
    if not cps or set_name != 'noto':
        return None
    return 'emoji_u' + '_'.join('%04x' % c for c in cps) + '.png'


def png_path(set_name, ch):
    n = png_name(set_name, ch)
    if not n:
        return None
    p = os.path.join(ASSETS, set_name, n)
    return p if os.path.exists(p) else None


def classify(ch):
    """按 Unicode 区块归类（对齐 CLDR 的 emoji 分组思路）。"""
    cps = cps_of(ch)
    if not cps:
        return 'symbols'
    if cps[0] == 0x1F3F3:
        return 'flags'
    if len(cps) == 2 and all(0x1F1E6 <= c <= 0x1F1FF for c in cps):
        return 'flags'

    c = cps[0]
    if (0x1F600 <= c <= 0x1F64F or 0x1F910 <= c <= 0x1F92F or 0x1F970 <= c <= 0x1F976
            or c == 0x1F97A or 0x1F479 <= c <= 0x1F480 or c == 0x1F48B):
        return 'faces'
    if (0x1F440 <= c <= 0x1F450 or 0x1F466 <= c <= 0x1F487 or 0x1F930 <= c <= 0x1F93F
            or 0x1F900 <= c <= 0x1F90F or c in (0x1F977, 0x1F9AF) or 0x270A <= c <= 0x270D):
        return 'people'
    if 0x1F400 <= c <= 0x1F43E or 0x1F980 <= c <= 0x1F9AE or 0x1F330 <= c <= 0x1F344:
        return 'animals'
    if 0x1F32D <= c <= 0x1F37F or 0x1F950 <= c <= 0x1F96F or 0x1F9C0 <= c <= 0x1F9CB:
        return 'food'
    if 0x1F300 <= c <= 0x1F320 or 0x1F3D4 <= c <= 0x1F3F0 or 0x1F5FA <= c <= 0x1F6FF:
        return 'travel'
    if 0x1F380 <= c <= 0x1F3D3 or 0x1F93C <= c <= 0x1F94C or c in (0x1F396, 0x1F397):
        return 'activity'
    if 0x1F4A0 <= c <= 0x1F5F9 or 0x1F9E0 <= c <= 0x1F9FF or c == 0x1F0CF:
        return 'objects'
    return 'symbols'


def build_catalog():
    """返回 (非空分类列表, {分类: [emoji]})；旗帜里跨性别/彩虹排最前。"""
    buckets = {key: [] for key, _ in CATEGORIES}
    for ch in EMOJIS:
        buckets[classify(ch)].append(ch)

    def norm(s):
        return ''.join(c for c in s if c not in '\ufe0f\ufe0e')

    special_keys = {norm('🏳️‍⚧'), norm('🏳️‍🌈')}
    specials = [s for s in buckets['flags'] if norm(s) in special_keys]
    rest = [s for s in buckets['flags'] if s not in specials]
    buckets['flags'] = specials + rest

    cats = [(k, label) for k, label in CATEGORIES if k == 'all' or buckets[k]]
    return cats, buckets


def load_atlas():
    """缩略图图集：一次解码，之后只裁切，避免逐个打开 512px PNG。"""
    png = os.path.join(ASSETS, 'thumb_atlas.png')
    idx = os.path.join(ASSETS, 'thumb_index.json')
    try:
        with open(idx, encoding='utf-8') as f:
            index = json.load(f)
        return Image.open(png).convert('RGBA'), index
    except Exception:
        return None, {}


def render_from_font(ch, size):
    """兜底：系统字体渲染（Noto 缺某个 emoji 时用）。"""
    pad = int(size * 0.16)
    box = size + pad * 2
    img = Image.new('RGBA', (box, box), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, size)
    except Exception:
        font = ImageFont.load_default()
    try:
        d.text((pad, pad), ch, font=font, embedded_color=True)
    except Exception:
        d.text((pad, pad), ch, font=font, fill=(0, 0, 0, 255))
    return img


_RAW_EMOJI_CACHE = {}


def render_emoji(set_name, ch, size):
    if set_name == 'noto':
        p = png_path('noto', ch)
        if p:
            try:
                raw = _RAW_EMOJI_CACHE.get(ch)
                if raw is None:
                    raw = Image.open(p).convert('RGBA')
                    if len(_RAW_EMOJI_CACHE) >= 64:      # 控制内存，约 60 MB 上限
                        _RAW_EMOJI_CACHE.clear()
                    _RAW_EMOJI_CACHE[ch] = raw
                h = max(1, int(size))
                w = max(1, int(raw.width * h / raw.height))
                return raw.resize((w, h), Image.LANCZOS)
            except Exception:
                pass
    return render_from_font(ch, size)


# ---------------------------------------------------------------- 贴纸


class Sticker:
    def __init__(self, kind, payload, cx, cy, size, set_name='noto', rot=0.0):
        self.kind = kind            # 'emoji' | 'meme' | 'image'
        self.payload = payload
        self.set_name = set_name
        self.cx = cx
        self.cy = cy
        self.size = size
        self.rot = float(rot)       # 旋转角度（度，顺时针为正）
        self._cache = {}

    def base_render(self):
        """未旋转的贴纸（按当前尺寸）。"""
        key = max(1, int(self.size))
        ck = ('base', key)
        if ck in self._cache:
            return self._cache[ck]

        if self.kind == 'emoji':
            img = render_emoji(self.set_name, self.payload, key)
        else:
            src = self.payload
            w = max(1, int(src.width * key / src.height))
            img = src.resize((w, key), Image.LANCZOS)

        self._cache = {ck: img}
        return img

    def render(self):
        """最终贴纸图（含旋转，画布会自动扩展）。"""
        size_key = max(1, int(self.size))
        rot_key = round(self.rot, 1)
        key = (size_key, rot_key)
        if key in self._cache:
            return self._cache[key]
        base = self.base_render()
        img = base.rotate(self.rot, expand=True, resample=Image.BICUBIC) if abs(self.rot) > 0.01 else base
        self._cache[key] = img
        return img

    def copy(self):
        return Sticker(self.kind, self.payload, self.cx, self.cy, self.size, self.set_name, self.rot)


# ---------------------------------------------------------------- 主界面


class App:
    def __init__(self, root):
        self.root = root
        self.base = None
        self.base_path = None
        self.stickers = []
        self.sel = -1
        self.scale = 1.0
        self.offset = (0, 0)
        self.gesture = None
        self.undo_stack = []
        self.thumb_cache = {}
        self._keep = []
        self._icon_refs = []
        self.category = 'all'
        self.disp_size = (1, 1)
        # 视图缩放（与贴纸缩放无关）
        self.view_zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.canvas_size = (1, 1)
        self._pan_start = None
        self._zoom_job = None
        self._pan_job = None

        self.cfg = load_config()
        try:
            self.font_scale = max(0.8, min(2.0, float(self.cfg.get('font_scale', 1.15))))
        except Exception:
            self.font_scale = 1.15
        self.theme_mode = self.cfg.get('theme', 'system')
        if self.theme_mode not in ('dark', 'light', 'system'):
            self.theme_mode = 'system'
        self.theme = resolve_theme(self.theme_mode)
        self.th = THEMES[self.theme]
        self.atlas, self.atlas_index = load_atlas()
        self.cats, self.buckets = build_catalog()

        try:
            dpi = root.winfo_fpixels('1i')
        except Exception:
            dpi = 96.0
        self.ui = max(1.0, dpi / 96.0)

        root.title(f'{APP} v{VER} · 表情工坊')
        root.configure(bg=self.th['bg'])
        self._build_ui()
        self._bind_keys()
        self._apply_geometry()
        self.root.after(4000, self._watch_system_theme)
        self.status('拖动移动 · 滚轮缩放 · 拖四角缩放、角外侧旋转 · [ ] 微调角度 · Del 删除 · Ctrl+Z 撤销')

    # --- 尺寸
    def px(self, v):
        return max(1, int(round(v * self.ui)))

    def fs(self, v):
        """字号：UI 缩放 × 用户字号倍率，返回负数（=像素）供 Tk 使用。"""
        return -max(9, int(round(v * self.ui * self.font_scale)))

    def font(self, size, bold=False):
        return ('Microsoft YaHei UI', self.fs(size), 'bold' if bold else 'normal')

    def _apply_geometry(self):
        self.root.geometry(f'{self.px(1200)}x{self.px(780)}')
        self.root.minsize(self.px(960), self.px(620))

    # ------------------------------------------------------------ UI
    def _build_ui(self):
        bar = tk.Frame(self.root, bg=self.th['panel'], height=self.px(56))
        bar.pack(side='top', fill='x')
        bar.pack_propagate(False)

        for text, cmd in (('新建空白', self.new_blank), ('打开照片', self.open_photo),
                          ('导入贴纸', self.add_image_sticker),
                          ('撤销', self.undo), ('删除', self.delete_selected), ('导出', self.export)):
            tk.Button(bar, text=text, command=cmd, bg=self.th['btn'], fg=self.th['text'],
                      activebackground=self.th['btn_hi'], activeforeground='#ffffff',
                      relief='flat', bd=0, padx=self.px(14), pady=self.px(6),
                      font=self.font(9), cursor='hand2').pack(side='left', padx=self.px(4), pady=self.px(8))

        # 右侧：A+ / 百分比 / A- / 主题（统一方形按钮，主题在 A- 左边留空）
        icon = self._text_icon('A+')
        self._icon_refs.append(icon)
        self.plus_btn = tk.Button(bar, image=icon, command=lambda: self.change_font(0.1),
                                  bg=self.th['btn'], activebackground=self.th['btn_hi'],
                                  relief='flat', bd=0, padx=self.px(6), pady=self.px(6), cursor='hand2')
        self.plus_btn.image = icon
        self.plus_btn.pack(side='right', padx=(self.px(2), self.px(10)), pady=self.px(8))

        self.size_label = tk.Label(bar, text=f'{int(round(self.font_scale * 100))}%', bg=self.th['panel'],
                                   fg=self.th['sub'], font=self.font(9), width=5)
        self.size_label.pack(side='right', padx=self.px(2), pady=self.px(8))

        icon = self._text_icon('A-')
        self._icon_refs.append(icon)
        self.minus_btn = tk.Button(bar, image=icon, command=lambda: self.change_font(-0.1),
                                   bg=self.th['btn'], activebackground=self.th['btn_hi'],
                                   relief='flat', bd=0, padx=self.px(6), pady=self.px(6), cursor='hand2')
        self.minus_btn.image = icon
        self.minus_btn.pack(side='right', padx=self.px(2), pady=self.px(8))

        icon = self._theme_icon()
        self._icon_refs.append(icon)
        self.theme_btn = tk.Button(bar, image=icon, command=self.cycle_theme,
                                   bg=self.th['btn'], activebackground=self.th['btn_hi'],
                                   relief='flat', bd=0, padx=self.px(6), pady=self.px(6), cursor='hand2')
        self.theme_btn.image = icon
        self.theme_btn.pack(side='right', padx=(self.px(10), self.px(6)), pady=self.px(8))

        # 快捷键说明按钮（外貌切换左边）
        icon = self._text_icon('?')
        self._icon_refs.append(icon)
        self.help_btn = tk.Button(bar, image=icon, command=self.show_shortcuts,
                                  bg=self.th['btn'], activebackground=self.th['btn_hi'],
                                  relief='flat', bd=0, padx=self.px(6), pady=self.px(6), cursor='hand2')
        self.help_btn.image = icon
        self.help_btn.pack(side='right', padx=(self.px(10), self.px(6)), pady=self.px(8))

        # 工具栏与内容之间的分隔线
        tk.Frame(self.root, bg=self.th['sep'], height=1).pack(side='top', fill='x')

        panel = tk.Frame(self.root, bg=self.th['panel'], width=self.px(370))
        panel.pack(side='right', fill='y')
        panel.pack_propagate(False)

        # 图片区与表情区之间的细分割线
        sep = tk.Frame(self.root, bg=self.th['sep'], width=1)
        sep.pack(side='right', fill='y')

        # 状态栏必须先于画布打包，否则会把画布挤窄
        self.statusbar = tk.Label(self.root, text='', bg=self.th['panel'], fg=self.th['sub'], anchor='w',
                                  font=self.font(8), padx=self.px(8))
        self.statusbar.pack(side='bottom', fill='x')

        self.canvas = tk.Canvas(self.root, bg=self.th['canvas'], highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)

        tk.Label(panel, text='Emoji', bg=self.th['panel'], fg=self.th['text'],
                 font=self.font(10, True)).pack(anchor='w', padx=self.px(12), pady=(self.px(10), self.px(4)))

        cat_bar = tk.Frame(panel, bg=self.th['panel'])
        cat_bar.pack(fill='x', padx=self.px(4), pady=(0, self.px(4)))
        per_row = 5
        for c in range(per_row):
            cat_bar.columnconfigure(c, weight=1, uniform='cat')
        self.cat_buttons = {}
        for i, (key, label) in enumerate(self.cats):
            r, col = divmod(i, per_row)
            b = tk.Button(cat_bar, text=label, command=lambda k=key: self.set_category(k),
                          bg=self.th['tab'], fg=self.th['sub'], activebackground=self.th['btn_hi'],
                          activeforeground=self.th['text'], relief='flat', bd=0,
                          font=self.font(8), padx=self.px(2), pady=self.px(3), cursor='hand2')
            b.grid(row=r, column=col, sticky='ew', padx=1, pady=1)
            self.cat_buttons[key] = b
        self._refresh_cats()

        self.grid_canvas = tk.Canvas(panel, bg=self.th['panel'], highlightthickness=0)
        sb = tk.Scrollbar(panel, orient='vertical', command=self.grid_canvas.yview)
        self.grid_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y', pady=self.px(6))
        self.grid_canvas.pack(side='left', fill='both', expand=True, padx=(self.px(8), 0), pady=self.px(6))

        self.grid_canvas.bind('<MouseWheel>',
                              lambda e: self.grid_canvas.yview_scroll(int(-e.delta / 120), 'units'))
        self.grid_canvas.bind('<Button-1>', self.on_grid_click)

        self.canvas.bind('<Button-1>', self.on_press)
        self.canvas.bind('<Double-Button-1>', self.on_double)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Motion>', self.on_motion)
        # 中键拖动平移视图
        self.canvas.bind('<Button-2>', self.on_pan_start)
        self.canvas.bind('<B2-Motion>', self.on_pan_move)
        self.canvas.bind('<ButtonRelease-2>', self.on_pan_end)
        self.canvas.bind('<MouseWheel>', self.on_wheel)
        self.canvas.bind('<Button-3>', self.on_right)
        self.canvas.bind('<Configure>', self._on_canvas_resize)

        self.build_grid()

    def _bind_keys(self):
        self.root.bind('<Control-o>', lambda e: self.open_photo())
        self.root.bind('<Control-s>', lambda e: self.export())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<Escape>', lambda e: self.select(-1))
        self.root.bind('<Control-plus>', lambda e: self.change_font(0.1))
        self.root.bind('<Control-equal>', lambda e: self.change_font(0.1))
        self.root.bind('<Control-minus>', lambda e: self.change_font(-0.1))
        self.root.bind('<Control-t>', lambda e: self.cycle_theme())
        self.root.bind('<bracketleft>', lambda e: self.rotate_selected(-5))
        self.root.bind('<bracketright>', lambda e: self.rotate_selected(5))
        # 层级
        self.root.bind('<Control-bracketright>', lambda e: self.raise_selected())
        self.root.bind('<Control-bracketleft>', lambda e: self.lower_selected())
        # 视图
        self.root.bind('<Control-Key-0>', lambda e: self.reset_view())
        self.root.bind('<Control-MouseWheel>', self.on_zoom_wheel)
        self.root.bind('<Key-0>', lambda e: self.reset_view())
        self.root.bind('<F1>', lambda e: self.show_shortcuts())

    def _on_canvas_resize(self, e):
        # 拖窗口时 <Configure> 会连续触发，防抖后再重绘，否则很卡
        job = getattr(self, '_resize_job', None)
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        self._resize_job = self.root.after(140, self._do_resize)

    def _do_resize(self):
        self._resize_job = None
        self.redraw_all()

    # ------------------------------------------------------------ 字号
    def change_font(self, delta):
        self.font_scale = round(max(0.8, min(2.0, self.font_scale + delta)), 2)
        self.cfg['font_scale'] = self.font_scale
        save_config(self.cfg)
        self.rebuild_ui()

    def rebuild_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        self._icon_refs = []
        self._keep = []
        self._build_ui()
        self._apply_geometry()
        self.redraw_all()

    def cycle_theme(self):
        order = ['dark', 'light', 'system']
        self.theme_mode = order[(order.index(self.theme_mode) + 1) % len(order)]
        self.theme = resolve_theme(self.theme_mode)
        self.th = THEMES[self.theme]
        self.cfg['theme'] = self.theme_mode
        save_config(self.cfg)
        self.root.configure(bg=self.th['bg'])
        self.rebuild_ui()
        self.status(f'主题：{THEME_LABELS[self.theme_mode]} {THEME_ICONS[self.theme_mode]}')

    def _watch_system_theme(self):
        """跟随系统模式下，系统切换浅/深色时自动跟着变。"""
        if self.theme_mode == 'system':
            want = system_theme()
            if want != self.theme:
                self.theme = want
                self.th = THEMES[want]
                self.root.configure(bg=self.th['bg'])
                self.rebuild_ui()
        self.root.after(4000, self._watch_system_theme)

    # ------------------------------------------------------------ 网格
    def _text_icon(self, text):
        s = self.px(30)
        img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        try:
            f = ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'),
                                                'Fonts', 'msyhbd.ttc'), int(s * 0.58))
        except Exception:
            f = ImageFont.load_default()
        try:
            box = d.textbbox((0, 0), text, font=f)
            w, h = box[2] - box[0], box[3] - box[1]
            d.text(((s - w) / 2 - box[0], (s - h) / 2 - box[1]), text, font=f, fill=self.th['text'])
        except Exception:
            d.text((s * 0.2, s * 0.2), text, font=f, fill=self.th['text'])
        return ImageTk.PhotoImage(img)

    def _theme_icon(self):
        """主题图标。系统模式用自绘显示器图标，保证像素级居中。"""
        s = self.px(30)
        img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        mode = self.theme_mode
        if mode == 'system':
            d = ImageDraw.Draw(img)
            col = self.th['text']
            w = s * 0.62          # 屏幕宽
            h = s * 0.40          # 屏幕高
            stand = s * 0.10      # 支架高
            gap = s * 0.05
            total = h + gap + stand
            top = (s - total) / 2
            x0 = (s - w) / 2
            lw = max(1, int(round(s * 0.07)))
            d.rounded_rectangle([x0, top, x0 + w, top + h],
                                radius=max(2, s * 0.08), outline=col, width=lw)
            cx = s / 2
            d.line([cx, top + h, cx, top + h + gap + stand], fill=col, width=lw)
            half = w * 0.28
            d.line([cx - half, top + h + gap + stand, cx + half, top + h + gap + stand],
                   fill=col, width=lw)
        else:
            emoji = '🌙' if mode == 'dark' else '☀️'
            try:
                e = render_emoji('noto', emoji, int(s * 0.9))
                box = e.getbbox()
                if box:
                    e = e.crop(box)
                e.thumbnail((int(s * 0.8), int(s * 0.8)), Image.LANCZOS)
                img.alpha_composite(e, ((s - e.width) // 2, (s - e.height) // 2))
            except Exception:
                pass
        return ImageTk.PhotoImage(img)

    def show_shortcuts(self):
        """快捷键总览。"""
        rows = [
            ('Ctrl + O', '打开照片'),
            ('Ctrl + S', '导出'),
            ('Ctrl + Z', '撤销（40 步）'),
            ('Ctrl + 滚轮', '视图缩放（光标为中心）'),
            ('中键拖动', '平移视图'),
            ('0', '视图复位'),
            ('滚轮（贴纸上）', '缩放贴纸'),
            ('拖动贴纸', '移动，并把它置顶'),
            ('四角方块拖动', '缩放贴纸'),
            ('四角外侧拖动', '旋转贴纸'),
            ('[ / ]', '旋转 ±5°'),
            ('Alt + 拖到贴纸上', '移到那层之上'),
            ('Ctrl + ]', '置于顶层'),
            ('Ctrl + [', '置于底层'),
            ('右键贴纸', '层级菜单 / 删除'),
            ('Delete', '删除贴纸'),
            ('Esc', '取消选中'),
            ('Ctrl + T', '切换主题'),
            ('Ctrl + + / -', '界面字号'),
            ('双击空白', '选择照片'),
        ]
        dlg = tk.Toplevel(self.root)
        dlg.title('快捷键')
        dlg.configure(bg=self.th['panel'])
        dlg.transient(self.root)
        px = self.px
        tk.Label(dlg, text='快捷键总览', bg=self.th['panel'], fg=self.th['text'],
                 font=self.font(11, True)).grid(row=0, column=0, columnspan=2, sticky='w',
                                                padx=px(18), pady=(px(14), px(8)))
        for r, (key, desc) in enumerate(rows, start=1):
            tk.Label(dlg, text=key, bg=self.th['panel'], fg=self.th['accent'],
                     font=self.font(9, True), anchor='e').grid(
                row=r, column=0, sticky='e', padx=(px(18), px(10)), pady=px(2))
            tk.Label(dlg, text=desc, bg=self.th['panel'], fg=self.th['sub'],
                     font=self.font(9), anchor='w').grid(
                row=r, column=1, sticky='w', padx=(0, px(18)), pady=px(2))
        tk.Button(dlg, text='知道了', command=dlg.destroy, bg=self.th['accent'], fg='#ffffff',
                  activebackground=self.th['accent'], relief='flat', bd=0,
                  font=self.font(9, True), padx=px(18), pady=px(6), cursor='hand2').grid(
            row=len(rows) + 1, column=0, columnspan=2, pady=(px(10), px(14)))
        dlg.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 3
        dlg.geometry(f'+{x}+{y}')

    def set_category(self, key):
        self.category = key
        self._refresh_cats()
        self.build_grid()

    def _refresh_cats(self):
        for k, b in getattr(self, 'cat_buttons', {}).items():
            active = (k == self.category)
            b.config(bg=self.th['accent'] if active else self.th['tab'],
                     fg='#ffffff' if active else self.th['sub'])

    def _grid_cols(self):
        """按面板实际宽度算列数，避免 emoji 被面板边缘裁掉。"""
        w = self.grid_canvas.winfo_width()
        if w < 60:
            w = self.px(300)
        cell = self._cell_px() + self.px(4)
        return max(3, int(w // max(1, cell)))

    def _cell_px(self):
        return self.px(44 * (1 + (self.font_scale - 1) * 0.5))

    def build_grid(self):
        c = self.grid_canvas
        c.delete('all')
        self._grid_positions = []

        items = []
        if self.category == 'all':
            # 全部：表情打头，旗帜收尾
            for key, _ in self.cats[1:]:
                items.extend(self.buckets.get(key, []))
        else:
            items.extend(self.buckets.get(self.category, []))

        if not items:
            c.create_text(self.px(20), self.px(20), anchor='nw', text='这个分类下没有内容',
                          fill=self.th['faint'], font=self.font(9))
            c.configure(scrollregion=(0, 0, 200, 60))
            return

        cols = self._grid_cols()
        cell = self._cell_px() + self.px(4)
        pad = self.px(2)
        n = 0
        for item in items:
            thumb = self._thumb(item)
            if thumb is None:
                continue
            col = n % cols
            row = n // cols
            x = pad + col * cell
            y = pad + row * cell
            c.create_image(x, y, image=thumb, anchor='nw')
            self._grid_positions.append((x, y, cell, item))
            n += 1

        rows = (n + cols - 1) // cols
        c.configure(scrollregion=(0, 0, cols * cell + pad, rows * cell + pad))
        c.yview_moveto(0)

    def on_grid_click(self, e):
        cx = self.grid_canvas.canvasx(e.x)
        cy = self.grid_canvas.canvasy(e.y)
        for x, y, cell, item in self._grid_positions:
            if x <= cx < x + cell and y <= cy < y + cell:
                self.add_emoji(item)
                return

    def _thumb(self, item):
        """从图集裁切缩略图（一次解码，之后全是内存操作）。"""
        side = self._cell_px()
        key = (item, side)
        if key in self.thumb_cache:
            return self.thumb_cache[key]
        img = None
        box = self.atlas_index.get(item)
        if self.atlas is not None and box:
            try:
                img = self.atlas.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
            except Exception:
                img = None
        if img is None:
            try:
                img = render_emoji('noto', item, side)
            except Exception:
                return None
        if img.size != (side, side):
            img = img.resize((side, side), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.thumb_cache[key] = photo
        return photo

    # ------------------------------------------------------------ 状态
    def status(self, msg):
        self.statusbar.config(text='  ' + msg)

    def push_undo(self):
        self.undo_stack.append([s.copy() for s in self.stickers])
        if len(self.undo_stack) > 40:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
        self.stickers = self.undo_stack.pop()
        self.sel = -1
        self.redraw_all()

    # ------------------------------------------------------------ 操作
    def open_photo(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                title='选择照片',
                filetypes=[('图片', '*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.heic *.heif *.avif'),
                           ('所有文件', '*.*')])
        if not path:
            return
        try:
            raw = Image.open(path)
            icc = raw.info.get('icc_profile')
            im = raw.convert('RGBA')
            if icc:
                im = apply_icc(im, icc)          # 转 sRGB，解决大图色差
        except Exception as e:
            messagebox.showerror(APP, f'打不开这张图：\n{e}')
            return
        self.base = im
        self.base_path = path
        self.stickers = []
        self.sel = -1
        self.undo_stack = []
        self.reset_view()
        self.status(f'{os.path.basename(path)} · {im.width}×{im.height} · 点 emoji 开始贴')

    def new_blank(self):
        """新建空白画布。"""
        dlg = tk.Toplevel(self.root)
        dlg.title('新建空白画布')
        dlg.configure(bg=self.th['panel'])
        dlg.transient(self.root)
        dlg.resizable(False, False)
        px = self.px
        w_var = tk.StringVar(value='1920')
        h_var = tk.StringVar(value='1080')
        bg_var = tk.StringVar(value='white')

        tk.Label(dlg, text='新建空白画布', bg=self.th['panel'], fg=self.th['text'],
                 font=self.font(11, True)).grid(row=0, column=0, columnspan=4, sticky='w',
                                                padx=px(16), pady=(px(14), px(4)))
        tk.Label(dlg, text='选个尺寸，或者自己填', bg=self.th['panel'], fg=self.th['sub'],
                 font=self.font(8)).grid(row=1, column=0, columnspan=4, sticky='w',
                                          padx=px(16), pady=(0, px(10)))

        presets = [('1080²', 1080, 1080), ('1920×1080', 1920, 1080),
                   ('2048²', 2048, 2048), ('A4 300dpi', 2480, 3508)]
        for i, (label, w, h) in enumerate(presets):
            tk.Button(dlg, text=label, command=lambda w=w, h=h: (w_var.set(str(w)), h_var.set(str(h))),
                      bg=self.th['btn'], fg=self.th['text'], activebackground=self.th['btn_hi'],
                      relief='flat', bd=0, font=self.font(8), padx=px(8), pady=px(5),
                      cursor='hand2').grid(row=2, column=i, padx=px(4), pady=px(4), sticky='ew')

        tk.Label(dlg, text='宽', bg=self.th['panel'], fg=self.th['sub'],
                 font=self.font(9)).grid(row=3, column=0, sticky='e', padx=(px(16), px(4)), pady=px(6))
        tk.Entry(dlg, textvariable=w_var, width=8, bg=self.th['btn'], fg=self.th['text'],
                 insertbackground=self.th['text'], relief='flat', font=self.font(9)).grid(
            row=3, column=1, sticky='w', pady=px(6))
        tk.Label(dlg, text='高', bg=self.th['panel'], fg=self.th['sub'],
                 font=self.font(9)).grid(row=3, column=2, sticky='e', padx=(px(8), px(4)), pady=px(6))
        tk.Entry(dlg, textvariable=h_var, width=8, bg=self.th['btn'], fg=self.th['text'],
                 insertbackground=self.th['text'], relief='flat', font=self.font(9)).grid(
            row=3, column=3, sticky='w', pady=px(6))

        tk.Label(dlg, text='背景', bg=self.th['panel'], fg=self.th['sub'],
                 font=self.font(9)).grid(row=4, column=0, sticky='e', padx=(px(16), px(4)), pady=px(6))
        for i, (val, label) in enumerate([('white', '白色'), ('transparent', '透明'), ('dark', '深灰')]):
            tk.Radiobutton(dlg, text=label, value=val, variable=bg_var, bg=self.th['panel'],
                           fg=self.th['text'], selectcolor=self.th['btn'], activebackground=self.th['panel'],
                           font=self.font(9), highlightthickness=0).grid(
                row=4, column=i + 1, sticky='w', padx=px(4), pady=px(6))

        def create():
            try:
                w = max(64, min(12000, int(float(w_var.get()))))
                h = max(64, min(12000, int(float(h_var.get()))))
            except Exception:
                messagebox.showerror(APP, '宽高要填数字哦', parent=dlg)
                return
            color = {'white': (255, 255, 255, 255),
                     'transparent': (0, 0, 0, 0),
                     'dark': (30, 32, 38, 255)}[bg_var.get()]
            self.base = Image.new('RGBA', (w, h), color)
            self.base_path = None
            self.stickers = []
            self.sel = -1
            self.undo_stack = []
            dlg.destroy()
            self.reset_view()
            self.status(f'空白画布 {w}×{h}')

        tk.Button(dlg, text='创建', command=create, bg=self.th['accent'], fg='#ffffff',
                  activebackground=self.th['accent'], relief='flat', bd=0,
                  font=self.font(10, True), padx=px(20), pady=px(7), cursor='hand2').grid(
            row=5, column=0, columnspan=4, pady=(px(10), px(14)))

        dlg.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 3
        dlg.geometry(f'+{x}+{y}')

    def add_emoji(self, ch):
        if self.base is None:
            messagebox.showinfo(APP, '先打开一张照片或新建空白画布吧 📷')
            return
        self.push_undo()
        size = int(self.base.height * 0.18)
        n = len(self.stickers)
        x = self.base.width // 2 + ((n % 5) - 2) * int(self.base.width * 0.05)
        y = self.base.height // 2 + ((n % 4) - 2) * int(self.base.height * 0.05)
        st = Sticker('emoji', ch, x, y, size, 'noto')
        self.stickers.append(st)
        self.sel = len(self.stickers) - 1
        # 只画新贴纸，不整屏重绘（粘贴更跟手）
        self.canvas.delete('selbox')
        self.draw_sticker(self.sel, st)
        self.draw_selection(st)

    def add_image_sticker(self):
        if self.base is None:
            messagebox.showinfo(APP, '先打开一张照片吧 📷')
            return
        path = filedialog.askopenfilename(title='选择 PNG 贴纸',
                                          filetypes=[('PNG', '*.png'), ('图片', '*.png *.webp *.jpg *.jpeg')])
        if not path:
            return
        try:
            im = Image.open(path).convert('RGBA')
        except Exception as e:
            messagebox.showerror(APP, f'打不开贴纸：\n{e}')
            return
        self.push_undo()
        size = int(self.base.height * 0.25)
        self.stickers.append(Sticker('image', im, self.base.width // 2, self.base.height // 2, size))
        self.sel = len(self.stickers) - 1
        self.redraw_all()

    def delete_selected(self):
        if 0 <= self.sel < len(self.stickers):
            self.push_undo()
            self.stickers.pop(self.sel)
            self.sel = -1
            self.redraw_all()

    def select(self, i):
        self.sel = i
        # 只更新选择框，不重绘整张底图
        self.canvas.delete('selbox')
        if 0 <= i < len(self.stickers):
            self.draw_selection(self.stickers[i])

    # ------------------------------------------------------------ 坐标 / 视图
    def fit(self):
        if self.base is None:
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 50 or ch < 50:
            cw, ch = self.px(880), self.px(620)
        self.canvas_size = (cw, ch)
        base_scale = min(cw / self.base.width, ch / self.base.height, 1.0)
        self.scale = base_scale * self.view_zoom
        dw = self.base.width * self.scale
        dh = self.base.height * self.scale
        self.offset = (cw / 2 + self.pan_x - dw / 2, ch / 2 + self.pan_y - dh / 2)
        self.disp_size = (max(1, int(dw)), max(1, int(dh)))

    def reset_view(self):
        self.view_zoom = 1.0
        self.pan_x = self.pan_y = 0.0
        self.redraw_all()
        self.status('视图复位到适应窗口')

    def on_zoom_wheel(self, e):
        if self.base is None:
            return
        self.fit()
        img_pt = self.canvas_to_img(e.x, e.y)
        factor = 1.15 if e.delta > 0 else 1 / 1.15
        self.view_zoom = max(0.2, min(6.0, self.view_zoom * factor))
        cw, ch = self.canvas_size
        base_scale = min(cw / self.base.width, ch / self.base.height, 1.0)
        self.scale = base_scale * self.view_zoom
        self.pan_x = e.x - cw / 2 - (img_pt[0] - self.base.width / 2) * self.scale
        self.pan_y = e.y - ch / 2 - (img_pt[1] - self.base.height / 2) * self.scale
        self.status(f'视图 {int(self.view_zoom * 100)}%  ·  0 复位')
        # 连续滚轮时合并重绘，避免每个事件都整屏重算
        self._schedule_redraw()

    def _schedule_redraw(self):
        if self._zoom_job:
            try:
                self.root.after_cancel(self._zoom_job)
            except Exception:
                pass
        self._zoom_job = self.root.after(18, self._flush_redraw)

    def _flush_redraw(self):
        self._zoom_job = None
        self.redraw_all()

    def on_pan_start(self, e):
        self._pan_start = (e.x, e.y, self.pan_x, self.pan_y)

    def on_pan_move(self, e):
        if not self._pan_start:
            return
        x0, y0, px, py = self._pan_start
        self.pan_x = px + (e.x - x0)
        self.pan_y = py + (e.y - y0)
        if self._pan_job:
            try:
                self.root.after_cancel(self._pan_job)
            except Exception:
                pass
        self._pan_job = self.root.after(18, self._flush_pan)

    def _flush_pan(self):
        self._pan_job = None
        self.redraw_all()

    def on_pan_end(self, e):
        self._pan_start = None

    def img_to_canvas(self, x, y):
        return (self.offset[0] + x * self.scale, self.offset[1] + y * self.scale)

    def canvas_to_img(self, x, y):
        return ((x - self.offset[0]) / self.scale, (y - self.offset[1]) / self.scale)

    # ------------------------------------------------------------ 绘制
    def _preview_base(self):
        """缓存一张不超过 2400px 的预览底图，缩小渲染时用它，避免每次重采样原图。"""
        pid = id(self.base)
        if getattr(self, '_preview', None) is not None and getattr(self, '_preview_id', None) == pid:
            return self._preview
        if self.base.width > 2400:
            r = 2400 / self.base.width
            prev = self.base.resize((2400, max(1, int(self.base.height * r))), Image.BILINEAR)
        else:
            prev = self.base
        self._preview, self._preview_id = prev, pid
        return prev

    def _draw_base(self):
        """只渲染可见区域：放大到 600% 也不会吃掉几个 G 内存。"""
        cw, ch = self.canvas_size
        s = self.scale
        ox, oy = self.offset
        x0 = max(0, int((-ox) / s))
        y0 = max(0, int((-oy) / s))
        x1 = min(self.base.width, int((cw - ox) / s) + 2)
        y1 = min(self.base.height, int((ch - oy) / s) + 2)
        if x1 <= x0 or y1 <= y0:
            return
        w = max(1, int((x1 - x0) * s))
        h = max(1, int((y1 - y0) * s))
        key = (x0, y0, x1, y1, w, h, id(self.base))
        if getattr(self, '_prev_key', None) == key and getattr(self, '_prev_img', None) is not None:
            tkimg = self._prev_img
        else:
            prev = self._preview_base()
            pf = prev.width / self.base.width
            if w <= prev.width * 1.02:
                # 目标尺寸不超过预览图 -> 直接用预览图取区域，快得多
                src = prev
                box = (int(x0 * pf), int(y0 * pf), int(x1 * pf) + 1, int(y1 * pf) + 1)
            else:
                src = self.base
                box = (x0, y0, x1, y1)
            crop = src.crop(box)
            if s < 1:
                f = int(1 / s)
                if f >= 2:
                    crop = crop.reduce(f)
            tkimg = ImageTk.PhotoImage(crop.resize((w, h), Image.BILINEAR))
            self._prev_key, self._prev_img = key, tkimg
        self.tk_base = tkimg
        self.canvas.create_image(ox + x0 * s, oy + y0 * s, image=tkimg, anchor='nw')

    def redraw_all(self):
        self.canvas.delete('all')
        if self.base is None:
            self.canvas.create_text(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2,
                                    text='双击这里选照片\n或点「打开照片」/「新建空白」',
                                    fill=self.th['hint'], font=self.font(13), justify='center')
            return
        self.fit()
        self._draw_base()

        self._keep = []
        for i, st in enumerate(self.stickers):
            self.draw_sticker(i, st)
            if i == self.sel:
                self.draw_selection(st)

    def _scale_for(self, st):
        """贴纸绘制比例；超大时封顶，防止 6x 视图把内存吃爆。"""
        s = self.scale
        img = st.base_render()
        m = max(img.width, img.height) or 1
        if m * s > 4096:
            s = 4096.0 / m
        return s

    def draw_sticker(self, i, st):
        img = st.render()
        s = self._scale_for(st)
        w = max(1, int(img.width * s))
        h = max(1, int(img.height * s))
        small = img.resize((w, h), Image.LANCZOS if s <= 1 else Image.BILINEAR)
        tkimg = ImageTk.PhotoImage(small)
        self._keep.append(tkimg)
        cx, cy = self.img_to_canvas(st.cx, st.cy)
        self.canvas.create_image(cx, cy, image=tkimg, anchor='center', tags=f's{i}')

    def _rot_pt(self, dx, dy, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return dx * c + dy * s, -dx * s + dy * c

    def _unrot_pt(self, dx, dy, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return dx * c - dy * s, dx * s + dy * c

    def _sel_geom(self, st):
        """返回 (画布中心, 半宽, 半高)。"""
        base = st.base_render()
        s = self._scale_for(st)
        hw = base.width * s / 2 + self.px(3)
        hh = base.height * s / 2 + self.px(3)
        cx, cy = self.img_to_canvas(st.cx, st.cy)
        return cx, cy, hw, hh

    def draw_selection(self, st):
        cx, cy, hw, hh = self._sel_geom(st)
        col = self.th['accent']
        pts = []
        for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            rx, ry = self._rot_pt(dx, dy, st.rot)
            pts.append((cx + rx, cy + ry))
        flat = []
        for px_, py_ in pts:
            flat.extend((px_, py_))
        self.canvas.create_polygon(flat, outline=col, fill='', width=2, tags='selbox')

        # 四角：小方块（缩放）+ 外侧 ↻ 图标（旋转）
        r = self.px(4)
        for px_, py_ in pts:
            self.canvas.create_rectangle(px_ - r, py_ - r, px_ + r, py_ + r,
                                         fill='#ffffff', outline=col, width=1, tags='selbox')
            dx, dy = px_ - cx, py_ - cy
            ln = max(1.0, (dx * dx + dy * dy) ** 0.5)
            gx = px_ + dx / ln * self.px(16)
            gy = py_ + dy / ln * self.px(16)
            self.canvas.create_text(gx, gy, text='↻', fill=col, tags='selbox',
                                    font=('Segoe UI Symbol', -max(9, self.px(10))))
        self._restack()

    def _restack(self):
        """让 canvas 堆叠顺序 = stickers 列表顺序（最后一个在最上）。

        拖动/缩放/旋转时会 delete + 重建贴纸图，重建后它会跑到最顶层，
        跟导出时按列表顺序合成的结果不一致 —— 这里统一纠正。
        """
        for i in range(len(self.stickers)):
            try:
                self.canvas.tag_raise(f's{i}')
            except Exception:
                pass
        try:
            self.canvas.tag_raise('selbox')
        except Exception:
            pass

    # ------------------------------------------------------------ 交互
    def hit(self, x, y):
        for i in range(len(self.stickers) - 1, -1, -1):
            st = self.stickers[i]
            base = st.base_render()
            s = self._scale_for(st)
            cx, cy = self.img_to_canvas(st.cx, st.cy)
            lx, ly = self._unrot_pt(x - cx, y - cy, st.rot)
            if abs(lx) <= base.width * s / 2 and abs(ly) <= base.height * s / 2:
                return i
        return -1

    # ------------------------------------------------------------ 层级
    def raise_selected(self):
        if 0 <= self.sel < len(self.stickers) - 1:
            self.push_undo()
            st = self.stickers.pop(self.sel)
            self.stickers.append(st)
            self.sel = len(self.stickers) - 1
            self.redraw_all()
            self.status('已置于顶层')

    def lower_selected(self):
        if 0 < self.sel < len(self.stickers):
            self.push_undo()
            st = self.stickers.pop(self.sel)
            self.stickers.insert(0, st)
            self.sel = 0
            self.redraw_all()
            self.status('已置于底层')

    def _corner_pts(self, st):
        cx, cy, hw, hh = self._sel_geom(st)
        pts = []
        for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            rx, ry = self._rot_pt(dx, dy, st.rot)
            pts.append((cx + rx, cy + ry))
        return (cx, cy), pts

    def _ang(self, cx, cy, e):
        return math.degrees(math.atan2(e.y - cy, e.x - cx))

    def on_press(self, e):
        if 0 <= self.sel < len(self.stickers):
            st = self.stickers[self.sel]
            (cx, cy), pts = self._corner_pts(st)
            # 四角：方块内=缩放，方块外一圈=旋转
            r = self.px(10)
            for px, py in pts:
                d = ((e.x - px) ** 2 + (e.y - py) ** 2) ** 0.5
                if d <= r:
                    self.gesture = {'mode': 'scale', 'i': self.sel, 's0': st.size,
                                    'd0': max(1.0, ((e.x - cx) ** 2 + (e.y - cy) ** 2) ** 0.5)}
                    return
                if d <= r + self.px(28):
                    self.gesture = {'mode': 'rotate', 'i': self.sel,
                                    'a0': self._ang(cx, cy, e), 'r0': st.rot}
                    return

        i = self.hit(e.x, e.y)
        self.select(i)
        if i >= 0:
            st = self.stickers[i]
            ix, iy = self.canvas_to_img(e.x, e.y)
            # 拖动即置顶（v1.7 的手感），同时把列表顺序也改掉，
            # 保证编辑时看到的层级和导出结果一致
            if i != len(self.stickers) - 1:
                self.push_undo()
                self.stickers.append(self.stickers.pop(i))
                i = len(self.stickers) - 1
                self.sel = i
                self.redraw_all()
            self.gesture = {'mode': 'move', 'i': i, 'dx': ix - st.cx, 'dy': iy - st.cy}

    def on_double(self, e):
        # 空白处双击 = 选照片
        if self.hit(e.x, e.y) < 0:
            self.open_photo()

    def on_drag(self, e):
        g = self.gesture
        if not g or g['i'] >= len(self.stickers):
            return
        i = g['i']
        st = self.stickers[i]

        if g['mode'] == 'rotate':
            cx, cy = self.img_to_canvas(st.cx, st.cy)
            a1 = self._ang(cx, cy, e)
            st.rot = (g['r0'] - (a1 - g['a0'])) % 360
        elif g['mode'] == 'scale':
            cx, cy = self.img_to_canvas(st.cx, st.cy)
            d = max(1.0, ((e.x - cx) ** 2 + (e.y - cy) ** 2) ** 0.5)
            limit = (self.base.height * 1.5) if self.base else 2000
            st.size = max(16, min(limit, g['s0'] * d / g['d0']))
        else:
            ix, iy = self.canvas_to_img(e.x, e.y)
            st.cx, st.cy = ix - g['dx'], iy - g['dy']

        st._cache = {}
        self.canvas.delete(f's{i}')
        self.canvas.delete('selbox')
        self.draw_sticker(i, st)
        self.draw_selection(st)

    def on_release(self, e):
        # 按住 Alt 拖到另一个贴纸上松开 = 把它移到那一层之上（拖拽改层级）
        g = self.gesture
        self.gesture = None
        if not g or g['mode'] != 'move':
            return
        try:
            alt = bool(e.state & 0x0008)      # Windows: Mod1 = Alt
        except Exception:
            alt = False
        if not alt:
            return
        i = g['i']
        if not (0 <= i < len(self.stickers)):
            return
        target = None
        for k in range(len(self.stickers) - 1, -1, -1):
            if k == i:
                continue
            st = self.stickers[k]
            base = st.base_render()
            s = self._scale_for(st)
            cx, cy = self.img_to_canvas(st.cx, st.cy)
            lx, ly = self._unrot_pt(e.x - cx, e.y - cy, st.rot)
            if abs(lx) <= base.width * s / 2 and abs(ly) <= base.height * s / 2:
                target = k
                break
        if target is None or target == i:
            return
        target_st = self.stickers[target]
        self.push_undo()
        st = self.stickers.pop(i)
        idx = self.stickers.index(target_st)      # 目标在移除后的新位置
        self.stickers.insert(idx + 1, st)         # 插到它上面
        self.sel = idx + 1
        self.redraw_all()
        self.status('已拖到该贴纸上层')

    def on_motion(self, e):
        """悬停时光标提示：角内=缩放，角外=旋转，贴纸上=拖动。"""
        cur = ''
        if 0 <= self.sel < len(self.stickers):
            st = self.stickers[self.sel]
            (cx, cy), pts = self._corner_pts(st)
            r = self.px(10)
            for px, py in pts:
                d = ((e.x - px) ** 2 + (e.y - py) ** 2) ** 0.5
                if d <= r:
                    cur = 'size_nw_se'
                    break
                if d <= r + self.px(28):
                    cur = 'exchange'
                    break
        if not cur and self.hit(e.x, e.y) >= 0:
            cur = 'hand2'
        if self.canvas.cget('cursor') != cur:
            self.canvas.config(cursor=cur)

    def rotate_selected(self, delta):
        if not (0 <= self.sel < len(self.stickers)):
            return
        st = self.stickers[self.sel]
        st.rot = (st.rot + delta) % 360
        st._cache = {}
        self.canvas.delete(f's{self.sel}')
        self.canvas.delete('selbox')
        self.draw_sticker(self.sel, st)
        self.draw_selection(st)
        self.status(f'旋转 {st.rot:.0f}°')

    def on_wheel(self, e):
        if not (0 <= self.sel < len(self.stickers)) or self.base is None:
            return
        # 只有鼠标真的停在选中的贴纸上才缩放，避免"滚一下 emoji 突然变小"
        if self.hit(e.x, e.y) != self.sel:
            return
        st = self.stickers[self.sel]
        factor = 1.1 if e.delta > 0 else 0.9
        st.size = max(16, min(self.base.height * 1.5, st.size * factor))
        st._cache = {}
        # 只重画这一个贴纸
        self.canvas.delete(f's{self.sel}')
        self.canvas.delete('selbox')
        self.draw_sticker(self.sel, st)
        self.draw_selection(st)

    def move_layer(self, delta):
        """上移/下移一层。"""
        if not (0 <= self.sel < len(self.stickers)):
            return
        j = self.sel + delta
        if not (0 <= j < len(self.stickers)):
            return
        self.push_undo()
        self.stickers[self.sel], self.stickers[j] = self.stickers[j], self.stickers[self.sel]
        self.sel = j
        self.redraw_all()
        self.status('上移一层' if delta > 0 else '下移一层')

    def on_right(self, e):
        """右键：层级菜单（原来直接删，容易误删）。"""
        i = self.hit(e.x, e.y)
        if i < 0:
            self.select(-1)
            return
        self.select(i)
        m = tk.Menu(self.root, tearoff=0, bg=self.th['panel'], fg=self.th['text'],
                    activebackground=self.th['accent'], activeforeground='#ffffff',
                    bd=0, font=self.font(9))
        m.add_command(label='置于顶层    Ctrl+]', command=self.raise_selected)
        m.add_command(label='上移一层', command=lambda: self.move_layer(1))
        m.add_command(label='下移一层', command=lambda: self.move_layer(-1))
        m.add_command(label='置于底层    Ctrl+[', command=self.lower_selected)
        m.add_separator()
        m.add_command(label='删除        Del', command=self.delete_selected)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    # ------------------------------------------------------------ 导出
    def render_full(self):
        out = self.base.copy()
        for st in self.stickers:
            img = st.render()
            out.alpha_composite(img, (int(st.cx - img.width / 2), int(st.cy - img.height / 2)))
        return out

    def export(self):
        if self.base is None:
            messagebox.showinfo(APP, '还没有照片可以导出呢 😅')
            return
        base_name = os.path.splitext(os.path.basename(self.base_path or 'photo'))[0]
        init_dir = os.path.dirname(self.base_path) if self.base_path else os.getcwd()
        path = filedialog.asksaveasfilename(
            title='导出', initialdir=init_dir, initialfile=f'{base_name}_paji.png',
            defaultextension='.png',
            filetypes=[('PNG（无损/透明）', '*.png'),
                       ('JPEG（高质量）', '*.jpg'),
                       ('WebP（体积小）', '*.webp'),
                       ('AVIF（更小）', '*.avif'),
                       ('TIFF（印刷）', '*.tif'),
                       ('BMP（兼容）', '*.bmp')])
        if not path:
            return
        out = self.render_full()
        ext = os.path.splitext(path)[1].lower()
        icc = srgb_profile_bytes()
        try:
            if ext in ('.jpg', '.jpeg'):
                kw = dict(quality=95, subsampling=1)
                if icc:
                    kw['icc_profile'] = icc
                out.convert('RGB').save(path, **kw)
            elif ext == '.webp':
                out.save(path, lossless=True, quality=100, method=6)
            elif ext == '.avif':
                out.save(path, quality=70, speed=6)
            elif ext in ('.tif', '.tiff'):
                kw = dict(compression='tiff_lzw')
                if icc:
                    kw['icc_profile'] = icc
                out.save(path, **kw)
            elif ext == '.bmp':
                out.convert('RGB').save(path)
            else:
                kw = dict(optimize=True)
                if icc:
                    kw['icc_profile'] = icc
                out.save(path, **kw)
        except Exception as e:
            messagebox.showerror(APP, f'导出失败：\n{e}')
            return
        self.status(f'已导出：{path}')


# ---------------------------------------------------------------- 自检


def selftest(out_path):
    enable_dpi_awareness()
    report = []
    root = tk.Tk()
    root.withdraw()
    app = App(root)

    noto_dir = os.path.join(ASSETS, 'noto')
    have = len([f for f in os.listdir(noto_dir) if f.endswith('.png')]) if os.path.isdir(noto_dir) else 0
    report.append(f'noto_files={have}')
    report.append(f'atlas={"ok" if app.atlas is not None else "missing"}')
    report.append(f'categories={len(CATEGORIES)}')

    cell = 200
    panels = []
    try:
        panels.append(('Noto', render_emoji('noto', '😻', cell - 40)))
    except Exception:
        pass

    strip = Image.new('RGBA', (cell * max(1, len(panels)), cell), (24, 25, 30, 255))
    d = ImageDraw.Draw(strip)
    try:
        label_font = ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'),
                                                     'Fonts', 'msyh.ttc'), 18)
    except Exception:
        label_font = ImageFont.load_default()
    for i, (label, img) in enumerate(panels):
        strip.alpha_composite(img, (i * cell + (cell - img.width) // 2, (cell - img.height) // 2))
        d.text((i * cell + 8, 6), label, fill=(220, 225, 235, 255), font=label_font)

    strip.convert('RGB').save(out_path)
    root.destroy()
    with open(out_path + '.ok.txt', 'w', encoding='utf-8') as f:
        f.write(' | '.join(report) + f'\nfont_scale={app.font_scale}\nsize={os.path.getsize(out_path)}')
    return 0 if have else 1


def main():
    enable_dpi_awareness()
    if '--selftest' in sys.argv:
        i = sys.argv.index('--selftest')
        out = sys.argv[i + 1] if len(sys.argv) > i + 1 else 'selftest.png'
        sys.exit(selftest(out))

    root = tk.Tk()
    app = App(root)
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        app.open_photo(sys.argv[1])
    root.mainloop()


if __name__ == '__main__':
    main()
