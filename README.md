# MiMo FREE · DMCTN

Bảng điều khiển CLI quản lý **MiMo CLI** (MiMoCode): đăng nhập Platform Pro, slot account, Chrome profile OAuth, reset machine ID — phát triển bởi **[DMCTN](https://github.com/dienlanhvietnam-lang)**.

<div align="center">

[![Release](https://img.shields.io/github/v/release/dienlanhvietnam-lang/dmctn-mimo?style=flat-square&logo=github&color=blue)](https://github.com/dienlanhvietnam-lang/dmctn-mimo/releases/latest)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC_BY--NC--ND_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![Stars](https://img.shields.io/github/stars/dienlanhvietnam-lang/dmctn-mimo?style=flat-square&logo=github)](https://github.com/dienlanhvietnam-lang/dmctn-mimo/stargazers)

**MiMo FREE v2.0.0 · Free MIMO 07/26**

</div>

---

## Tính năng

- Dashboard CLI (panel) — chọn thao tác bằng số `[0]`–`[8]`
- **Đăng nhập MiMo Platform** qua Chrome profile + OAuth (`mimo providers login`)
- **Quản lý slot** Pro động — lưu / kích hoạt / đổi tài khoản MiMo
- **Context Vault** — snapshot / restore ngữ cảnh local (`memory`, DB)
- **Chọn hồ sơ Chrome** mặc định cho OAuth
- **Reset ID máy MiMo** — 3 chế độ (wipe / preserve context / registry only)
- **Reset hoàn toàn MiMo** — DB, memory, session, auth (giữ slot; tùy chọn snapshot)
- **Reset sâu** — xóa thêm slot + `.config/mimocode` (mặc định giữ vault)
- Đa ngôn ngữ (vi, en)
- Tự migrate config từ `.mimo-vip` / `.mino-vip` → `.dmctn-mimo`

## Menu chính

| # | Thao tác |
|---|----------|
| 0 | Thoát |
| 1 | Đổi ngôn ngữ |
| 2 | Chọn hồ sơ Chrome |
| 3 | Đặt lại ID máy MiMo CLI *(3 chế độ)* |
| 4 | Đặt lại hoàn toàn MiMo CLI *(giữ slot)* |
| 5 | Đăng nhập MiMo Platform |
| 6 | Quản lý account MiMo |
| 7 | Reset sâu *(xóa slot + `.config/mimocode`)* |
| 8 | Quản lý Context Vault |

## Yêu cầu

| Thành phần | Ghi chú |
|------------|---------|
| **Python 3.10+** | Chạy dashboard `main.py` |
| **Google Chrome** | OAuth Platform (profile Gmail đã login) |
| **Node.js + npm** | Cài MiMo CLI trong thư mục `mimo/` |

## Cài đặt nhanh

### 1. Clone repo

```bash
git clone https://github.com/dienlanhvietnam-lang/dmctn-mimo.git
cd dmctn-mimo
```

### 2. Cài MiMo CLI bundle

```bash
cd mimo
npm install
cd ..
```

### 3. Chạy dashboard

**Windows** — double-click hoặc terminal:

| File | Mục đích |
|------|----------|
| `start.bat` | Mở dashboard MiMo FREE (`main.py`) |
| `mimo.bat` | Gọi MiMo CLI từ thư mục gốc (tự `npm install` nếu thiếu) |

```bat
start.bat
```

**Linux / macOS**

```bash
python main.py
```

### 4. Luồng khuyến nghị (lần đầu)

1. Menu **2** — chọn Chrome profile (Gmail + [platform.xiaomimimo.com](https://platform.xiaomimimo.com) đã đăng nhập)
2. Menu **5** — đăng nhập OAuth → tạo slot Pro
3. Menu **6** — kích hoạt / đổi slot
4. Chạy MiMo chat: `mimo/start.bat`

## MiMo CLI (terminal AI)

```bat
mimo\start.bat
```

Các shortcut trong `mimo/`:

| File | Mục đích |
|------|----------|
| `start.bat` | Mở MiMo CLI |
| `login_platform.bat` | OAuth / menu 5 |
| `manage_accounts.bat` | Quản lý slot / menu 6 |
| `manage_context.bat` | Context Vault / menu 8 |
| `reset_machine.bat` | Reset ID máy / menu 3 |
| `totally_reset.bat` | Reset toàn bộ / menu 4 |
| `deep_reset.bat` | Reset sâu / menu 7 |
| `setup_auto.bat` | Cấu hình MiMo Auto |

Repo pin **`@mimo-ai/cli` 0.1.5** (trong `mimo/package.json`). Sau khi pull, chạy lại `cd mimo && npm install` nếu CLI cũ.

### Lỗi `actor tool` / `Delegating...` (workaround)

Khi dùng agent **Build + MiMo Auto**, đôi khi xuất hiện lỗi đỏ:

```text
The actor tool was called with invalid arguments.
Invalid input: expected object, received string  (path: operation)
```

**Nguyên nhân:** bug upstream MiMo-Code — model gửi tham số `operation` dạng string thay vì object khi spawn subagent ([issue #417](https://github.com/XiaomiMiMo/MiMo-Code/issues/417), [#561](https://github.com/XiaomiMiMo/MiMo-Code/issues/561)). Không phải lỗi code dự án Python trong repo này.

**Giảm lỗi:**

1. Giữ CLI **≥ 0.1.5**: `cd mimo && npm install`
2. **`setup_mimo_auto.py`** (menu reset / `mimo/setup_auto.bat`) mặc định **`permission.task: deny`** trên agent Build — không spawn subagent, tránh lỗi `actor`
3. Prompt cụ thể, tránh kích hoạt delegate: *"Đọc file X, grep Y — **không delegate subagent**"*
4. Task quét repo lớn → ưu tiên **Cursor Agent** thay vì MiMo Build
5. Bật lại subagent (tự chịu rủi ro): sửa `~/.config/mimocode/mimocode.jsonc`, xóa block `permission.task` trong `agent.build`

## Context Vault (ngữ cảnh local)

Lưu / khôi phục `memory/`, `mimocode.db`, `storage/`, `snapshot/` vào:

```
Documents/.dmctn-mimo/context/
  context_manifest.json
  bundles/*.tar.gz
```

- **Menu 8** — list / tạo snapshot / activate / rename / delete
- **Menu 3** — chọn chế độ reset (giữ hoặc xóa context)
- Vault nằm **ngoài** `mimocode/` nên không bị xóa nhầm bởi wipe thường

**Disclaimer:** chỉ nhớ **local** (~75–85% khả thi). **Không** cam kết MiMo Auto trên server vẫn nhớ phiên sau khi đổi `mimo-free-client` (phụ thuộc Xiaomi).

## So sánh reset

| | Menu 3 (wipe) | Menu 3 (preserve) | Menu 3 (registry) | Menu 4 | Menu 7 |
|---|:---:|:---:|:---:|:---:|:---:|
| Machine ID mới | ✓ | ✓ | — | ✓ | ✓ |
| Đổi registry | ✓ | ✓ | ✓ | ✓ | ✓ |
| Snapshot / restore context | — | ✓ | — | tùy chọn | tùy chọn |
| Xóa `auth.json` active | ✓ | ✓ | — | ✓ | ✓ |
| Xóa DB / memory / session | — | —* | — | ✓ | ✓ |
| Giữ slot `accounts/` | ✓ | ✓ | ✓ | ✓ | — |
| Xóa Context Vault | — | — | — | — | tùy chọn (mặc định giữ) |
| Xác nhận `YES` | — | — | — | — | ✓ |

\* Preserve: memory được restore sau khi đổi ID.

Sau reset: dùng **MiMo Auto** (Tab trong CLI) hoặc đăng nhập lại menu **5**. Restore context: menu **8**.

## Cấu hình

File config:

```
Documents/.dmctn-mimo/config.ini
```

Mục quan trọng:

```ini
[Chrome]
chromepath = C:\Program Files\Google\Chrome\Application\chrome.exe
profile_directory = Profile 10
profile_display_name = Ten hien thi

[Utils]
language = vi
enabled_update_check = True
```

Biến môi trường (tùy chọn):

| Biến | Ý nghĩa |
|------|---------|
| `DMCTN_MIMO_LANG` | Ngôn ngữ UI (`vi`, `en`, …) |
| `DMCTN_MIMO_KEEP_RUNNING` | Không đóng Chrome khi OAuth |
| `DMCTN_MIMO_*` / `DMCTN_MIMO_*` | Tương thích bản cũ |

## Kiểm tra / phát triển

Chạy trực tiếp bằng Python (không cần file `.bat` riêng):

```bash
python scripts/e2e_smoke_test.py --json
python scripts/phase_loop.py --json
python scripts/phase_loop.py --fix --loop   # auto-fix đến khi pass (tùy chọn)
```

Đóng gói `.exe` (maintainer, Windows): `python build.py` (cần PyInstaller + `build.spec`).

## Báo lỗi & đóng góp

- Issues: [github.com/dienlanhvietnam-lang/dmctn-mimo/issues](https://github.com/dienlanhvietnam-lang/dmctn-mimo/issues)
- Org DMCTN: [github.com/dienlanhvietnam-lang](https://github.com/dienlanhvietnam-lang)

## License

[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) — xem [LICENSE.md](LICENSE.md).

Tool chỉ phục vụ học tập và nghiên cứu; người dùng tự chịu trách nhiệm khi sử dụng.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dienlanhvietnam-lang/dmctn-mimo&type=Date)](https://star-history.com/#dienlanhvietnam-lang/dmctn-mimo&Date)
