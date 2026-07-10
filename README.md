# MiMo FREE · DMCTN

Bảng điều khiển CLI quản lý **MiMo CLI** (MiMoCode): đăng nhập Platform Pro, slot account, Chrome profile OAuth, reset machine ID — phát triển bởi **[DMCTN](https://github.com/dienlanhvietnam-lang)**.

<div align="center">

[![Release](https://img.shields.io/github/v/release/dienlanhvietnam-lang/dmctn-mimo?style=flat-square&logo=github&color=blue)](https://github.com/dienlanhvietnam-lang/dmctn-mimo/releases/latest)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC_BY--NC--ND_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![Stars](https://img.shields.io/github/stars/dienlanhvietnam-lang/dmctn-mimo?style=flat-square&logo=github)](https://github.com/dienlanhvietnam-lang/dmctn-mimo/stargazers)

**MiMo FREE v0.1 · Free MIMO 07/26**

</div>

---

## Tính năng

- Dashboard CLI (panel) — chọn thao tác bằng số `[0]`–`[7]`
- **Đăng nhập MiMo Platform** qua Chrome profile + OAuth (`mimo providers login`)
- **Quản lý slot** Pro động — lưu / kích hoạt / đổi tài khoản MiMo
- **Chọn hồ sơ Chrome** mặc định cho OAuth
- **Reset ID máy MiMo** — anonymous channel / MiMo Auto
- **Reset hoàn toàn MiMo** — DB, memory, session, auth (giữ slot)
- **Reset sâu** — xóa thêm slot + `.config/mimocode`
- Đa ngôn ngữ (vi, en)
- Tự migrate config từ `.mimo-vip` / `.mino-vip` → `.dmctn-mimo`

## Menu chính

| # | Thao tác |
|---|----------|
| 0 | Thoát |
| 1 | Đổi ngôn ngữ |
| 2 | Chọn hồ sơ Chrome |
| 3 | Đặt lại ID máy MiMo CLI |
| 4 | Đặt lại hoàn toàn MiMo CLI *(giữ slot)* |
| 5 | Đăng nhập MiMo Platform |
| 6 | Quản lý account MiMo |
| 7 | Reset sâu *(xóa slot + `.config/mimocode`)* |

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

**Windows**

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
| `reset_machine.bat` | Reset ID máy / menu 3 |
| `totally_reset.bat` | Reset toàn bộ / menu 4 |
| `deep_reset.bat` | Reset sâu / menu 7 |
| `setup_auto.bat` | Cấu hình MiMo Auto |

## So sánh reset

| | Menu 3 | Menu 4 | Menu 7 |
|---|:---:|:---:|:---:|
| Machine ID mới | ✓ | ✓ | ✓ |
| Xóa `auth.json` active | ✓ | ✓ | ✓ |
| Xóa DB / memory / session | — | ✓ | ✓ |
| Giữ slot `accounts/` | ✓ | ✓ | — |
| Xóa `.config/mimocode` | — | — | ✓ |
| Xác nhận `YES` | — | — | ✓ |

Sau reset: dùng **MiMo Auto** (Tab trong CLI) hoặc đăng nhập lại menu **5**.

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

```bash
python scripts/e2e_smoke_test.py --json
python scripts/phase_loop.py --json
```

## Báo lỗi & đóng góp

- Issues: [github.com/dienlanhvietnam-lang/dmctn-mimo/issues](https://github.com/dienlanhvietnam-lang/dmctn-mimo/issues)
- Org DMCTN: [github.com/dienlanhvietnam-lang](https://github.com/dienlanhvietnam-lang)

## License

[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) — xem [LICENSE.md](LICENSE.md).

Tool chỉ phục vụ học tập và nghiên cứu; người dùng tự chịu trách nhiệm khi sử dụng.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dienlanhvietnam-lang/dmctn-mimo&type=Date)](https://star-history.com/#dienlanhvietnam-lang/dmctn-mimo&Date)
