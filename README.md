# Paji · 啪叽 v1.8.6-beta 😻

> 打开一张照片（或新建空白画布），往上贴 emoji / 表情 / PNG 贴纸，导出成图。

**单文件 exe · 绿色免安装**

> 许可证：本项目代码为 **MIT**；第三方素材许可见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
> 内置素材只有 Noto Color Emoji（OFL 1.1）与公有领域国旗。

---

## v1.8.6

- 🗑️ **彻底移除 Epic Face**（版权不明的迷因素材）：贴纸面板不再有它，
  相关代码（`meme_files` / `add_meme` / `Sticker('meme')`）一并删除
- 📦 现在内置素材只有 **Noto emoji + 国旗**，来源与许可完全清晰
- 原图已备份到 `C:\dsh-work\素材箱\epicface_备份.png`（不进软件、不进仓库）

## v1.8.5

- 😻 **图标换成 Noto 的 😻（U+1F63B）**：多尺寸缩放生成，OFL 许可可随包分发
- 之前的自绘笑脸图标不再使用

## v1.8.4

- 🎨 **图标改为自绘**：纯代码绘制黄色笑脸（`tools_make_icon.py`），不再依赖任何第三方美术
- 🧹 **公开仓库合规**：`.gitignore` 排除 `assets/meme/`；`PAJI_PUBLIC=1` 构建时自动跳过该素材
- 📄 新增 `LICENSE`（MIT）、`THIRD-PARTY-NOTICES.md`、`licenses/`（四种许可证原文）

## v1.8.3 修复

- 🖱️ **拖动即置顶**：恢复到 v1.7 的手感 —— 拖哪个贴纸，它就跑到最上层；
  同时**列表顺序同步修改**，所以导出结果和编辑时完全一致（不再是"看着在上面、导出在下面"）
- ❓ **新增快捷键按钮**：工具栏外观按钮左边多了一个 `?`，点开显示全部快捷键（`F1` 同效）
- 🖥️ **系统图标重绘**：跟随系统模式不再用 emoji，改为 PIL 自绘显示器图标，像素级居中

## v1.8.2 修复

- 右键贴纸弹层级菜单：置于顶层 / 上移一层 / 下移一层 / 置于底层 / 删除
- `Alt + 拖到贴纸上`：移到那层之上
- 粘贴加速（只画新贴纸 + 解码缓存），连续粘 10 个 115 ms
- 修掉"滚一下 emoji 突然变小"（现在只有光标在贴纸上才缩放）

## v1.8.1 修复

- 遮挡关系与导出一致（`_restack()`）
- 大图缩放：2400px 预览缓存 + 18ms 合并重绘 + 整数倍 reduce，6000×4000 实测 12–49 ms

## v1.8 新增

- 新建空白画布（1080² / 1920×1080 / 2048² / A4 / 自定义，白·透明·深灰）
- 视图缩放 `Ctrl+滚轮`（20%–600%）、中键平移、`0` 复位
- ICC 校色（Adobe RGB/ProPhoto → sRGB）
- 6 种导出格式：PNG / JPEG / WebP 无损 / AVIF / TIFF / BMP
- emoji 1008 个

## 原有功能

- 打开照片（JPG/PNG/WebP/BMP/TIFF）；画布空白处双击也能选图
- 10+1 个分类：全部 / 最近 / 表情 / 人物 / 动物 / 食物 / 旅行 / 活动 / 物品 / 符号 / 旗帜
- 拖动移动、滚轮缩放、**四角拖拽缩放 / 角外侧拖拽旋转**（PS 风格变换框）
- 高 DPI 适配；字号可调（`A-` / 百分比 / `A+`）；主题三选一（浅 / 深 / 跟随系统）
- 导出按**原图分辨率**合成

## 首次准备素材

仓库**不包含** 21 MB 的 emoji 图片（1009 个 PNG 上传太慢），克隆后先下载：

```powershell
python tools_fetch_emoji.py     # 下载 Noto emoji + 国旗（约 1-3 分钟）
python tools_build_thumbs.py    # 生成缩略图图集
python paji.py                  # 运行
```

## 快捷键

| 键 | 作用 |
|---|---|
| `Ctrl+O` | 打开照片 |
| `Ctrl+S` | 导出 |
| `Ctrl+Z` | 撤销（40 步） |
| `Ctrl` + 滚轮 | **视图缩放** |
| 中键拖动 | **平移视图** |
| `0` | 视图复位 |
| `Ctrl+]` / `Ctrl+[` | 置顶 / 置底 |
| `[` / `]` | 旋转 ±5° |
| `Delete` | 删除选中贴纸 |
| `Esc` | 取消选中 |
| 滚轮 | 缩放选中的贴纸 |

设置文件：`%APPDATA%\Paji\config.json`（字号、主题、最近使用）。

---

## 开发

```powershell
python paji.py                              # 跑源码
python paji.py --selftest selftest.png      # 无窗口自检
python tools_build_emoji_list.py            # 生成清单（按分类配额）
python tools_fetch_emoji.py                 # 下载 Noto + 国旗
python tools_build_thumbs.py                # 生成缩略图图集
python tools_make_intro.py                  # 生成介绍图
python compat_test.py                       # 兼容性测试
```

### 打包

```powershell
.buildenv\Scripts\python.exe -m PyInstaller --noconfirm --clean "Paji.spec"
```

产物：`dist\Paji v1.8.0-beta.exe`（42.2 MB）。

> 注意：`Paji.spec` 里 `EXCLUDE_ASSETS` 控制哪些素材不进 exe（如 TW 旗素材保留但不打包）。

---

## 版本归档（重要约定）

> **每个发布过的版本都永久保留，不覆盖、不删除。**

```
Paji\
├── dist\        只放当前版本（构建输出）
├── releases\    全部历史版本 exe（永久保留）+ README 索引
└── versions\    每个版本的完整源码快照（永久保留）+ INDEX.md
```

- 打包后自动归档 **exe**（`tools_archive.py`）和 **源码快照**（`tools_snapshot.py`）
- 手动执行：`.buildenv\Scripts\python.exe tools_archive.py` / `tools_snapshot.py`
- 同名已存在时跳过，不覆盖
- 目前已归档：`v1.7.4`、`v1.8.0-beta`

> 本机没装 git，所以用 `versions\` 做轻量版本控制：每个版本一份完整源码副本 + sha1 清单。
> 以后装了 Git，可以直接 `git init` 并把这些快照作为初始提交。

---

## 变更记录

**v1.8.0-beta**
- 新增：空白画布、视图缩放/平移、贴纸层级、ICC 校色、6 种导出格式、最近分类
- emoji 801 → **1008**
- 版本号带 `-beta` 后缀

**v1.7.4** 四角缩放/旋转改图标提示；修复编码事故
**v1.7.3** 四角缩放 + 角外旋转
**v1.7.2** 贴纸旋转（PS 变换框）
**v1.7.1** 修复工具栏按钮空白
**v1.7** 分类标签、图集加速
**v1.6** Canvas 网格 + 缩略图图集
**v1.5~v1.0** 见 HANDOFF

*Paji v1.8.0-beta · 2026-11-09*
