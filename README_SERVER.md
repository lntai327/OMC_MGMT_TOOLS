# Hướng Dẫn Triển Khai OMC Management Tools Lên Server

Bộ phát hành này đã được đóng gói hoàn toàn độc lập (Self-contained). Không cần cài đặt Python, Node.js hay bất kỳ mã nguồn nào trên Server. Chỉ cần cài sẵn **Docker** và **Docker Compose**.

---

## 1. Yêu cầu hệ thống trên Server
- **Hệ điều hành**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+) hoặc Windows Server.
- **Docker**: phiên bản 24.0+
- **Docker Compose**: phiên bản 2.20+ (hoặc plugin `docker compose`)
- Các cổng mạng cần mở:
  - `80` (HTTP - tự redirect sang HTTPS)
  - `443` (HTTPS)
  - `5432` (PostgreSQL - nếu cần kết nối từ ngoài)

---

## 2. Kiến trúc Compose Stacks trên Production

Hệ thống Production được tách thành **2 Docker Compose Stack độc lập** dùng chung mạng Docker `omc_network`:
1. **PostgreSQL Persistence Stack (`docker-compose.postgres.yml`)**:
   - Chạy container cơ sở dữ liệu `postgres` độc lập.
   - Gắn volume lưu trữ lâu dài `omc_postgres_data`.
   - Không bị ảnh hưởng, không bị tắt khi cập nhật hoặc dừng ứng dụng web.
2. **Application Stack (`docker-compose.prod.yml`)**:
   - Chạy `backend`, `redis`, `celery_worker`, `celery_beat`, `frontend` (Nginx SSL HTTPS).
   - Tự động kết nối tới PostgreSQL qua mạng nội bộ `omc_network`.

---

## 3. Các bước triển khai

### Bước 1: Xuất gói cài đặt (trên máy build)
```powershell
.\run.ps1 export
```

### Bước 2: Nạp Docker images trên Server
Giải nén gói release và nạp images:
```bash
unzip omc_release_*.zip
cd release_bundle_*
chmod +x deploy.sh
./deploy.sh load
```

### Bước 3: Cấu hình môi trường (Tùy chọn)
Nếu cần đổi mật khẩu database, cổng hay secret key, sao chép và sửa file `.env`:
```bash
cp .env.example .env
nano .env
```
*(Nếu bỏ qua bước này, hệ thống sẽ tự dùng cấu hình mặc định).*

### Bước 4: Khởi động hệ thống
```bash
./deploy.sh up
```
Lệnh trên sẽ tự động:
1. Tạo bridge network `omc_network` (nếu chưa có).
2. Khởi động PostgreSQL stack (`docker-compose.postgres.yml`).
3. Khởi động Application stack (`docker-compose.prod.yml`).
4. Backend tự động chạy Alembic migration để tạo cấu trúc bảng database mới nhất.
5. Tự động seed tài khoản admin mặc định.
6. Khởi động Celery Worker, Celery Beat và Web Frontend Nginx (SSL HTTPS).

---

## 4. Quản trị dịch vụ

| Thao tác | Lệnh Linux (`./deploy.sh`) | Lệnh Windows (`.\deploy.ps1`) |
| :--- | :--- | :--- |
| **Xem trạng thái cả 2 stacks** | `./deploy.sh ps` | `.\deploy.ps1 ps` |
| **Xem logs ứng dụng** | `./deploy.sh logs` | `.\deploy.ps1 logs` |
| **Xem logs PostgreSQL** | `./deploy.sh logs postgres` | `.\deploy.ps1 postgres logs` |
| **Khởi động lại ứng dụng** | `./deploy.sh restart` | `.\deploy.ps1 restart` |
| **Dừng ứng dụng (giữ nguyên DB)** | `./deploy.sh down` | `.\deploy.ps1 down` |
| **Dừng toàn bộ (cả ứng dụng & DB)** | `./deploy.sh down --all` | `.\deploy.ps1 down -All` |
| **Quản lý riêng PostgreSQL** | `./deploy.sh postgres [up\|down\|restart\|logs\|ps]` | `.\deploy.ps1 postgres [up\|down\|restart\|logs\|ps]` |

> **Lưu ý về dữ liệu:**
> Toàn bộ dữ liệu PostgreSQL (`omc_postgres_data`), Redis (`omc_redis_data`) và tệp tải lên/xuất báo cáo (`omc_backend_data`) được lưu trong **Docker Named Volumes**. Khi bạn chạy `down` hay cập nhật phiên bản, toàn bộ dữ liệu trên không bao giờ bị mất.
