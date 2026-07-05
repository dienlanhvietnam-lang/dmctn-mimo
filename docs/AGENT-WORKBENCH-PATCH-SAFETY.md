# Báo cáo lỗi treo Cursor UI — hướng dẫn cho Agent

> **Mục đích:** Ghi lại sự cố ngày 2026-07-05 để agent làm việc trong repo này **không tái phạm** patch phá `workbench.desktop.main.js`.
>
> **Đọc file này trước** khi sửa `workbench_patches.py`, chạy VIP activate, `apply_all_patches.py`, hoặc `loop_fix.bat`.

---

## Tóm tắt sự cố

| Mục | Chi tiết |
|-----|----------|
| **Ngày** | 2026-07-05 ~03:27 (UTC+7) |
| **Triệu chứng** | Cursor mở được nhưng UI trống/treo (chỉ thấy khung tối, không sidebar/editor) |
| **Cursor cài tại** | `E:\cursor31\cursor\` (xem `Documents\.mino-vip\config.ini` → `[WindowsPaths] cursor_path`) |
| **File bị hỏng** | `{cursor_path}\out\vs\workbench\workbench.desktop.main.js` |
| **Nguyên nhân** | Patch `getTeams` dùng `return[];/*` — mở block comment `/*` trong bundle minified |
| **Hậu quả** | `SyntaxError: Unexpected token '{'` → workbench không load |
| **Khôi phục** | Copy từ `workbench.desktop.main.js.vip.*.bak` (bản trước patch) + sửa patch trong repo |

---

## Nguyên nhân kỹ thuật (chi tiết)

### Patch lỗi (đã bị loại bỏ — KHÔNG được dùng lại)

```python
# ❌ CẤM — đã gây treo UI
'async getTeams(){this.authDebugLog("getTeams: called");const n=await this.dashboardClient()': (
    'async getTeams(){return[];/*'
),
```

### Vì sao `/*` nguy hiểm?

File `workbench.desktop.main.js` là **một dòng/minified ~47MB**. Khi chèn `/*`:

1. Parser JS coi mọi thứ sau đó là **comment** cho đến khi gặp `*/`.
2. Trong bundle có hàng nghìn chuỗi chứa `*/` (ví dụ template `` `**/${n}/` `` trong `transformRepoPatternToGlobalPattern`).
3. Comment đóng **sớm** (~17KB sau), nuốt mất khối code auth/service.
4. Phần code còn lại bị **cắt cụt** → `SyntaxError` tại ~dòng 26164.
5. Cursor không parse được workbench → **màn hình trống vĩnh viễn**.

### Patch an toàn (hiện tại trong repo)

```python
# ✅ ĐÚNG — early return, giữ phần còn lại của hàm (dead code nhưng hợp lệ cú pháp)
'async getTeams(){this.authDebugLog("getTeams: called");const n=await this.dashboardClient()': (
    'async getTeams(){return[];const n=await this.dashboardClient()'
),
```

---

## Quy tắc bắt buộc cho Agent

### 1. Cấm dùng block comment để “noop” hàm

| Cấm | Thay bằng |
|-----|-----------|
| `return;/*` | `return;` hoặc `return[];` + giữ phần match gốc phía sau |
| `/* ... */` bọc thân hàm | Early return: `async fn(){return;` hoặc `async fn(){return X;` |
| Comment nhiều dòng trong patch string | Chỉ patch đúng substring đã verify tồn tại trong workbench |

**Lý do:** Minified bundle chứa `*/` ở mọi nơi; không kiểm soát được phạm vi comment.

### 2. Luôn chạy syntax check sau khi patch

```powershell
node --check "E:\cursor31\cursor\resources\app\out\vs\workbench\workbench.desktop.main.js"
```

- Exit code **0** = OK.
- Exit code **≠ 0** → **khôi phục backup ngay**, không commit patch.

### 3. Luôn backup trước khi ghi workbench

Repo đã có logic backup trong `cursor_membership.py` (`*.vip.{timestamp}.bak`). Agent **không được** ghi đè workbench nếu:

- Chưa có backup mới, hoặc
- `node --check` chưa pass trên nội dung sẽ ghi.

### 4. Verify không thay thế syntax check

Script `scripts/verify_sync_block.py` chỉ kiểm tra **chuỗi con có tồn tại**. Patch có thể “pass verify” nhưng vẫn **SyntaxError** (sự cố 2026-07-05 là ví dụ).

**Bắt buộc:** `verify_*.py` **+** `node --check`.

### 5. Patch rủi ro cao — cần review thêm

Các patch sau có thể gây side effect (không treo UI như `/*`, nhưng có thể lỗi auth/usage):

| Patch | Rủi ro |
|-------|--------|
| `async refreshAuthentication(){return}` | Chặn hoàn toàn refresh auth lúc khởi động |
| `this.refreshMembership=async()=>{return;` | Membership không sync từ server |
| `async performFetch(...){return;` | Usage/limit UI có thể không cập nhật |

Khi thêm patch mới trong nhóm này: test mở Cursor + đăng nhập + mở workspace thực tế.

### 6. Đóng Cursor trước khi patch/restore (trừ khi cố ý)

`cursor_membership.py` ghi workbench khi Cursor đang chạy có thể fail (file lock) hoặc Cursor giữ bản hỏng trong RAM.

- Patch/restore: **đóng hết `Cursor.exe`** trước.
- `MINO_VIP_KEEP_RUNNING=1` trong `start.bat` / `loop_fix.bat` — biết rủi ro file lock.

---

## Checklist trước khi merge thay đổi patch

```
[ ] Không có `/*` mở comment trong replacement string (trừ `/*je();*/` đã verify an toàn — comment đóng ngay)
[ ] Mỗi replacement là substring thật trong workbench (dùng scripts/rescan_workbench.py hoặc grep)
[ ] python scripts/verify_antirevert.py
[ ] python scripts/verify_sync_block.py
[ ] node --check <workbench.desktop.main.js>  ← BẮT BUỘC
[ ] Có file backup *.bak / *.vip.*.bak mới
[ ] Ghi rõ phiên bản Cursor (vd. 3.9.16 tại E:\cursor31\cursor)
```

---

## Khôi phục khẩn cấp khi UI trống/treo

### Triệu chứng nhận diện

- Cửa sổ Cursor mở, nền tối, không menu/editor.
- `node --check` trên workbench báo `SyntaxError`.

### Các bước

1. **Đóng hết Cursor** (Task Manager → End task `Cursor.exe`).
2. Chạy restore:
   ```bat
   restore.bat
   ```
   hoặc:
   ```powershell
   python scripts\restore_workbench.py
   ```
3. Nếu restore script không tìm được bản sạch, copy tay backup gần nhất **không chứa** patch sync:
   ```
   workbench.desktop.main.js.vip.20260705_032703.bak
   → workbench.desktop.main.js
   ```
4. Xác nhận:
   ```powershell
   node --check "...\workbench.desktop.main.js"
   ```
5. Mở lại Cursor.

### Phân biệt backup

| File | Ý nghĩa |
|------|---------|
| `*.vip.{timestamp}.bak` | Backup **trước** lần patch VIP (thường sạch nhất) |
| `*.backup.{timestamp}` / `*.cfv.*.bak` | Có thể là bản **đã patch** — không dùng restore nếu cùng size/nội dung với bản hỏng |
| `*.broken.{timestamp}.bak` | Do `restore_workbench.py` lưu khi sửa |

---

## File liên quan trong repo

| File | Vai trò |
|------|---------|
| `workbench_patches.py` | **Nguồn patch** — sửa ở đây |
| `cursor_membership.py` | Apply patch + backup + ghi workbench (nội bộ reset/register) |
| `apply_all_patches.py` | Script apply thủ công (dev) |
| `scripts/verify_sync_block.py` | Verify chuỗi sync block |
| `scripts/verify_antirevert.py` | Verify patch membership PRO |
| `scripts/restore_workbench.py` | Khôi phục khẩn cấp |
| `restore.bat` | Wrapper restore (Windows) |
| `scripts/phase_loop.py` | 12 phase — gọi verify + auto-fix |
| `loop_fix.bat` | Chạy phase loop |

Config đường dẫn Cursor: `%USERPROFILE%\Documents\.mino-vip\config.ini`

---

## Lịch sử sửa sau sự cố (2026-07-05)

1. **`workbench_patches.py`:** `getTeams` đổi từ `return[];/*` → `return[];const n=await this.dashboardClient()`.
2. **`scripts/verify_sync_block.py`:** Check `getTeams noop` đổi từ `return[];/*` → `return[];`.
3. **Workbench tại `E:\cursor31\cursor`:** Đã restore từ `.vip.20260705_032703.bak`, `node --check` pass.

---

## Gợi ý cải tiến (chưa implement)

Agent có thể đề xuất/thêm nếu cần:

- Tích hợp `node --check` vào `phase_loop.py` (phase 13).
- Từ chối apply nếu replacement chứa mẫu `/{2}` không đóng (regex đơn giản: `/*` không theo sau bởi `*/` trong cùng chuỗi replacement).
- Lưu hash workbench pre/post patch trong log.

---

*Cập nhật: 2026-07-05 — sự cố treo UI do patch `getTeams` với block comment `/*`.*
