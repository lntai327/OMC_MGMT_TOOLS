# Hướng Dẫn Kiểm Thử Thủ Công (User Manual Testing Guide)
## VNPT TPNV OMC Report Tools Platform

Tài liệu này cung cấp các bước chi tiết để bạn kiểm thử toàn bộ hệ thống sau khi khởi chạy ứng dụng web.

---

## 1. Khởi chạy toàn bộ hệ thống

Mở terminal PowerShell tại thư mục gốc của dự án:
```powershell
.\run.ps1 build
```
*(hoặc dùng lệnh Docker Compose tiêu chuẩn: `docker compose -f docker/docker-compose.yml up --build -d`)*

Kiểm tra trạng thái các container:
```powershell
.\run.ps1 ps
```
Bạn sẽ thấy 5 container đều ở trạng thái `running` (hoặc `healthy`):
1. `postgres` (PostgreSQL 16)
2. `redis` (Redis 7)
3. `backend` (FastAPI Web Server)
4. `celery_worker` (Celery Worker)
5. `celery_beat` (Celery Watchdog & Cleanup)
6. `frontend` (React + Vite + Tailwind CSS)

---

## 2. Các kịch bản kiểm thử (Test Cases)

### Kịch bản 1: Kiểm tra kết nối & API Health Check
1. Mở trình duyệt truy cập: `http://localhost:8000/docs` (FastAPI Swagger UI).
2. Tìm nhóm **Health & Diagnostics**, mở `GET /api/v1/health` và bấm **Try it out** -> **Execute**.
3. **Kết quả mong đợi:**
   - Mã HTTP: `200 OK`.
   - Nội dung trả về có:
     ```json
     {
       "status": "healthy",
       "database": "connected",
       "redis": "connected",
       "db_latency_ms": 1.25,
       "redis_latency_ms": 0.85
     }
     ```

---

### Kịch bản 2: Đăng nhập & Xác thực JWT + Phân quyền RBAC
1. Truy cập giao diện Web: `http://localhost:3000`.
2. Hệ thống sẽ tự động hiển thị màn hình **Đăng nhập**.
3. Nhập tài khoản mặc định được khởi tạo tự động:
   - **Tài khoản:** `admin`
   - **Mật khẩu:** `demo`
4. Bấm **Đăng nhập hệ thống**.
5. **Kết quả mong đợi:**
   - Đăng nhập thành công, chuyển hướng vào màn hình **Danh mục Báo cáo** (`HomePage`).
   - Thanh điều hướng trên cùng hiển thị thông tin người dùng: `admin` và huy hiệu vai trò `ADMIN`.
   - Token JWT được lưu trữ an toàn trong `localStorage`.

---

### Kịch bản 3: Tra cứu & Quản lý Megawan / Metronet
1. Tại trang chủ, chọn thẻ **"Quản lý Megawan & Metronet"** (bấm *Mở module*).
2. **Thêm mới bản ghi:**
   - Bấm nút **"Thêm mới"** ở thanh công cụ góc phải.
   - Nhập thông tin thử nghiệm:
     - *Mã Thuê Bao:* `TB_TEST_001`
     - *Tên thuê bao:* `Khách hàng VNPT Test 01`
     - *Địa chỉ:* `123 Đường Trần Phú, Quy Nhơn`
     - *Loại hình TB:* `MEGAWAN`
     - *Loại kênh:* `FTTH`
     - *Tốc độ:* `100 Mbps`
     - *SVLAN/CVLAN:* `100/200`
     - *IP:* `10.10.1.1`
     - *Tên hệ thống:* `SW_QUYNHON_01`
   - Bấm **"Lưu bản ghi"**.
   - **Kết quả mong đợi:** Bản ghi mới xuất hiện ngay đầu bảng với nhãn trạng thái và ngày cập nhật tự động.
3. **Bộ lọc & Tìm kiếm:**
   - Nhập `Test` vào ô **Tìm kiếm 'Tất cả'**: bảng chỉ hiển thị bản ghi có chứa từ khóa `Test`.
   - Xóa bộ lọc hoặc nhập cụ thể vào ô **Tên hệ thống**: bảng phản hồi lọc dữ liệu chính xác.
4. **Sửa bản ghi:**
   - Bấm biểu tượng cây bút (Sửa) tại dòng vừa tạo.
   - Đổi tên thuê bao thành `Khách hàng VNPT Test Đã Sửa` và bấm **Lưu bản ghi**.
   - Kiểm tra dòng tương ứng đã được cập nhật nội dung.
5. **Xóa bản ghi:**
   - Bấm biểu tượng thùng rác (Xóa).
   - Hệ thống hiển thị hộp thoại xác nhận. Bấm OK để xác nhận xóa.
   - Kiểm tra bản ghi biến mất khỏi bảng.

---

### Kịch bản 4: Kiểm thử Import Excel Bất đồng bộ (Async Job + Progress Bar)
1. Trên trang Megawan, bấm nút **"Import Excel"**.
2. Chọn một tệp Excel mẫu (có thể dùng tệp mẫu `storage/templates/Megawan Metronet-template.xlsx` hoặc tệp dữ liệu thực tế).
3. Bấm **"Bắt đầu Import"**.
4. **Kết quả mong đợi:**
   - API trả về ngay lập tức mã `202 Accepted` kèm theo `job_id` trong vòng chưa đầy 100ms (không bị đơ giao diện).
   - Một modal popup hiển thị tiến trình thời gian thực:
     - Thanh tiến độ chạy từ `0%` -> `25%` -> `50%` -> `75%` -> `100%` qua kết nối WebSocket (hoặc cơ chế polling 3 giây).
     - Khi hoàn tất, hiển thị thông báo thành công và chi tiết kết quả (Tổng số dòng, Thành công, Lỗi/Bỏ qua).
   - Danh sách bảng dữ liệu được cập nhật đầy đủ các dòng mới.

---

### Kịch bản 5: Kiểm thử Export Excel Bất đồng bộ & Tải file
1. Trên trang Megawan, chọn một điều kiện lọc bất kỳ (ví dụ nhập `MEGAWAN` vào Loại hình TB, hoặc để trống để xuất toàn bộ).
2. Bấm nút **"Export Excel"**.
3. **Kết quả mong đợi:**
   - Giao diện kích hoạt popup tiến trình xử lý nền (Celery worker).
   - Worker trích xuất dữ liệu, định dạng theo file mẫu và lưu vào thư mục `storage/exports/`.
   - Khi thanh tiến trình đạt `100%`, nút xanh **"Tải file báo cáo (.xlsx)"** xuất hiện.
4. Bấm vào nút **"Tải file báo cáo (.xlsx)"**.
5. Mở file `.xlsx` vừa tải về bằng Microsoft Excel:
   - Các cột tiêu đề, font chữ và dữ liệu khớp chính xác với kết quả lọc.

---

### Kịch bản 6: Kiểm tra Worker Concurrency & Watchdog Tự Động
1. Xem log hoạt động của Celery Worker:
   ```powershell
   docker compose -f docker/docker-compose.yml logs -f celery_worker
   ```
   Bạn sẽ thấy thông báo nhận việc `process_import` và `process_export`, sử dụng `FOR UPDATE SKIP LOCKED` an toàn không có hiện tượng race condition hay deadlock.
2. Xem log của Celery Beat:
   ```powershell
   docker compose -f docker/docker-compose.yml logs -f celery_beat
   ```
   Bạn sẽ thấy:
   - Task `check_stalled_jobs` chạy mỗi 2 phút để bắt các tác vụ quá hạn timeout.
   - Task `purge_old_files` chạy mỗi giờ để tự động dọn dẹp các file tạm > 24 giờ.

---

## 3. Lệnh dừng hệ thống khi hoàn tất

```powershell
.\run.ps1 down
```
*(hoặc: `docker compose -f docker/docker-compose.yml down`)*

