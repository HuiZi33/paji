# 第三方素材与组件许可（THIRD-PARTY NOTICES）

Paji 的**源代码**采用 MIT（见 `LICENSE`）。但项目随包分发了一些第三方素材与运行时组件，
它们各有自己的许可，本文件逐一说明。完整许可原文见 `licenses/` 目录。

> 一句话结论：**除 Epic Face（见第 5 节）外，其余全部可合法再分发。**

---

## 1. Noto Color Emoji（emoji 图片）

- 来源：<https://github.com/googlefonts/noto-emoji>
- 版权：Copyright 2013 Google LLC
- 许可：**SIL Open Font License 1.1**（`licenses/OFL-1.1.txt`）
- 用途：`assets/noto/*.png`（1008 个 emoji 图片）+ 由其生成的 `assets/thumb_atlas.png`
- OFL 允许随软件分发、修改与再分发，要求：
  - 随附 OFL 许可原文与版权声明 ✅（本文件 + `licenses/`）
  - 不得单独售卖字体文件本身
  - **保留字体名称（Reserved Font Name）**：若修改字体需改名；本项目的图片做了缩放拼接，
    属于"文档/美术资源使用"，不再以 Noto 名义发布字体，故不受此条约束
- 说明：本项目不分发 `.ttf` 字体文件，只分发从该仓库导出的 PNG 图片

## 2. 国旗图片（region flags）

- 来源：`noto-emoji/third_party/region-flags`（原始素材取自 Wikimedia Commons）
- 许可：**公有领域（Public Domain）** 或各国法律规定的公有领域
  （`licenses/region-flags-LICENSE.txt`，其中列出了少数需特别说明的国家）
- 用途：`assets/noto/emoji_u1f1e6_*.png` 等国旗图片
- 备注：本项目**未包含** TW 旗（按项目所有者要求排除），排除行为不构成侵权

## 3. 彩虹旗 / 跨性别旗

- 来源：`noto-emoji/2D/png/512`（ZWJ 序列图片）
- 许可：随 Noto 项目，**OFL 1.1**
- 备注：旗帜图案本身（彩虹旗、跨性别旗）通常被视为**无版权或放弃版权**的公共符号

## 4. Pillow / Python / Tcl-Tk

| 组件 | 许可 | 说明 |
|---|---|---|
| Pillow | **MIT-CMU**（`licenses/Pillow-MIT-CMU.txt`） | 图像处理库 |
| Python 3.12 | PSF License | 解释器 |
| Tcl/Tk 8.6 | BSD-style | GUI 运行时 |

以上均允许随二进制程序再分发，PyInstaller 打包时已将其许可文本一并处理。

## 5. Epic Face 迷因素材（❌ 已从软件中彻底移除）

- 文件：原 `assets/meme/epicface.png`
- 调查结果：这是 **Awesome Face / Epic Smiley** 网络迷因（[Know Your Meme](https://knowyourmeme.com/memes/awesome-face-epic-smiley)），
  **未找到任何适用于该图片的自由许可**
  - Wikimedia Commons 上的 [File:Epic Face.png](https://commons.wikimedia.org/wiki/File:Epic_Face.png)
    是**另一个作品**（215×287，某人照片上叠加笑脸，作者 narfman10a，GFDL + CC BY-SA），
    与本项目曾使用的透明 PNG **不是同一张图**
  - 各图库网站的 "Free Download" 只代表下载免费，**不是授权**
- 处理（2026-11-10）：
  - **已从软件中删除**：素材文件、`meme_files()`、`add_meme()`、`Sticker('meme')` 全部分支
  - 原图备份在项目外：`C:\dsh-work\素材箱\epicface_备份.png`（不进仓库、不进 exe）
  - 图标：`icon.ico` 由 **Noto Color Emoji 的 😻（U+1F63B）** 生成，OFL 1.1

## 6. PyInstaller 引导程序（bootloader）

- 来源：<https://pyinstaller.org>
- 许可：**GPL v2 + 特殊例外条款**（`licenses/PyInstaller-COPYING.txt`）
- 关键点：该例外明确允许把**未修改的** bootloader 打包进任意许可的应用程序，
  且不要求你的程序也变成 GPL —— 所以分发 `Paji.exe` 合法
- 要求：随附其许可声明 ✅（本文件 + `licenses/PyInstaller-COPYING.txt`）

## 7. 项目内其他内容

| 内容 | 归属 | 说明 |
|---|---|---|
| `paji.py`、`tools_*.py`、`.spec`、`.cmd` | 本项目作者 | MIT |
| `intro.png` 中的照片 | 项目作者的摄影作品（_DSC9970） | 需作者确认可公开；若不确定可换成纯色/渐变背景 |
| `emoji_list.py`、`emoji_names.json` | 由 Noto 文件名列表生成 | 仅为文件名集合，不含美术资源 |
| `flag_codes.json` | ISO 3166 国家代码清单 | 事实性数据，无版权 |
| 系统字体（微软雅黑 / Segoe UI Emoji） | 微软 | **未随包分发**，仅运行时调用 |

---

## 发布前检查清单

- [x] 源代码许可文件（MIT）
- [x] 第三方素材许可原文归档（`licenses/`）
- [x] 国旗/彩虹旗合规（公有领域 / OFL）
- [x] PyInstaller 例外条款确认
- [x] **Epic Face 已从公开仓库排除**（`.gitignore` + `PAJI_PUBLIC=1` 构建开关）
- [x] 图标改为自绘（无第三方素材）
- [x] `intro.png` / `intro2.png` 中的照片为项目作者本人摄影作品（2026-11-10 确认）
- [ ] 仓库中加入本文件与 `LICENSE`（上传时一并提交）

*最后更新：2026-11-10*
