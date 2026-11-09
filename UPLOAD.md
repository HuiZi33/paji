# 上传到 GitHub（纯浏览器版）

> 不需要 git、不需要 GitHub Desktop。仓库现在只有 **28 个文件**，浏览器一次拖完。

---

## 1. 上传前：这些文件才要传

在 `C:\dsh-work\Paji` 里，**只选下面这些**（Ctrl+点选 / 框选）：

```
LICENSE
THIRD-PARTY-NOTICES.md
README.md
UPLOAD.md
.gitignore
paji.py
emoji_list.py
Paji.spec
build.cmd
icon.ico
icon_preview.png
compat_test.py
test_degraded.py
flag_codes.json
emoji_names.json
tools_archive.py
tools_build_emoji_list.py
tools_build_thumbs.py
tools_check_exe.py
tools_fetch_emoji.py
tools_make_icon.py
tools_make_intro.py
tools_make_promo2.py
tools_snapshot.py
licenses/            ← 整个文件夹（4 个 txt）
```

**不要传**（`.gitignore` 已排除，看不到也无所谓）：

| 路径 | 原因 |
|---|---|
| `.buildenv/` | 40 MB 虚拟环境 |
| `.buildtmp/` `build/` | 打包中间产物 |
| `dist/` | 42 MB exe → 走 Release |
| `releases/` `versions/` | 本地归档 |
| `assets/` | 21 MB 素材，用脚本下载 |
| `__pycache__/` | 缓存 |

> 为什么不含素材？1009 个 PNG 在浏览器里上传非常慢。仓库只放代码，别人克隆后跑一行命令就能下载全部素材（见 README 的「首次准备素材」）。

---

## 2. 建仓库

1. 打开 <https://github.com/new>
2. Repository name：`paji`（或 `Paji`）
3. 选 **Public**
4. **不要**勾 "Add a README file"（我们已经有了）
5. License 选 **MIT License**
6. 点 **Create repository**

## 3. 上传文件（一次搞定）

1. 在新仓库页点 **"uploading an existing file"**
2. 打开资源管理器，进入 `C:\dsh-work\Paji`
3. **框选第 1 节列出的文件**（含 `licenses` 文件夹），拖进浏览器
4. 等进度条走完（28 个文件很快）
5. 底部 Commit changes 填：`Paji v1.8.6-beta: initial public release`
6. 点 **Commit changes**

> 网页上传支持拖文件夹，`licenses/` 直接拖进去即可，层级会保留。

## 4. 仓库设置

仓库页右上 **Settings**：

- **Description**：`Windows 表情工坊：照片上贴 emoji / 贴纸，四角缩放旋转，原图分辨率导出`
- **Topics**：`emoji` `photo-editor` `python` `tkinter` `windows` `sticker`
- **License**：应已识别为 MIT（因为传了 LICENSE）

---

## 5. 发 Release（放 exe）

1. 仓库页右侧 **Releases → Create a new release**
2. **Choose a tag** → 输入 `v1.8.6-beta` → 点 "Create new tag"
3. Release title：`Paji v1.8.6-beta`
4. 描述里粘贴 README 的「v1.8.6 / v1.8.5 / v1.8.4」段落
5. 把本机 `C:\dsh-work\Paji\dist\Paji v1.8.6-beta.exe`（42.0 MB）拖进 **Attach binaries**
6. 点 **Publish release**

> GitHub 单文件上限 2 GB，42 MB 没问题。

---

## 6. 别人克隆后怎么跑

```powershell
# 1. 下载素材（1009 个 emoji，约 1-3 分钟）
python tools_fetch_emoji.py

# 2. 生成缩略图图集
python tools_build_thumbs.py

# 3. 运行
python paji.py
```

打包 exe：双击 `build.cmd`（会自动建虚拟环境 + 拉素材 + 建图集 + 打包 + 归档）。

---

## 7. 上传前自检

- [x] `LICENSE`（MIT）
- [x] `THIRD-PARTY-NOTICES.md`（Explain 了 emoji/国旗/PyInstaller 的许可）
- [x] `licenses/` 4 份许可原文
- [x] 图标是 Noto 😻（OFL），无版权不明素材
- [x] Epic Face 已从软件与仓库移除
- [x] 宣传图照片为本人作品
- [x] 代码里没有本机用户名 / 私钥

*最后更新：2026-11-10*
