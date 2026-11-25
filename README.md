#
## 1. App Architecture & Tech Stack

### Architecture Guidelines

* **Strict Separation of Concerns:** Decoupled frontend and backend communicating via REST API and WebSockets.
* **Frontend:** MVVM (Model-View-ViewModel) architectural pattern.
* **Backend:** Clean Architecture utilizing the **Service-Repository pattern**.

### Technology Stack

* **Frontend:** React.js, Vite, Tailwind CSS
* **Backend:** Python 3.13+, FastAPI, SQLAlchemy (Async), OAuth2 with JSON Web Tokens (JWT), Role-Based Access Control (RBAC)
* **Database:** PostgreSQL (with database abstraction layer to maintain compatibility with Microsoft SQL Server for future switching if needed)
* **Real-Time Communication:** WebSockets
* **Deployment Package:** Docker & Docker Compose

---

## 2. Performance & User Experience

* Implement asynchronous request handling and non-blocking background workers for heavy operations.
* Provide interactive loading indicators and real-time progress updates for long-running tasks:
* Server connection verification
* Large Excel import/export processing
* Heavy database batch updates

---

## 3. Asynchronous Long-Running Task Architecture (Import/Export Pipeline)

To prevent server bottlenecks and request timeouts when multiple concurrent users handle large datasets, all heavy import and export operations must follow an **Async Job + Polling/WebSocket** workflow.

### A. Database Schema (PostgreSQL)

Create a `jobs` table to track the state, progress, and metadata of all asynchronous operations:

```sql
CREATE TYPE job_type AS ENUM ('import', 'export');
CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    type job_type NOT NULL,
    status job_status DEFAULT 'pending',
    progress INT DEFAULT 0, -- Completion percentage (0 - 100)
    input_file_path TEXT, -- Original file path (for imports)
    output_file_path TEXT, -- Resulting file path (for exports)
    result_meta JSONB, -- Detailed execution metadata (successful rows, error counts, etc.)
    error_message TEXT, -- Error log if the task fails
    timeout_at TIMESTAMP WITH TIME ZONE, -- Task expiration timeout timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimized indexes for worker polling and user status lookups
CREATE INDEX idx_jobs_status_type ON jobs(status, type);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);

```

### B. API Endpoints Design

#### 1. Create Job Endpoint (`POST /api/v1/jobs`)

* **Functionality:** Accepts file uploads or export parameters, creates a job record with `pending` status, and immediately returns `202 Accepted` with the `job_id`.
* **Response Sample (`202 Accepted`):**
```json
{
  "job_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "status": "pending",
  "message": "Job accepted and queued for processing."
}

```



#### 2. Check Job Status Endpoint (`GET /api/v1/jobs/{id}`)

* **Functionality:** Client polls this endpoint every 3–5 seconds (or listens via WebSockets) to update progress bars or retrieve download URLs upon completion.
* **Response Sample (Processing):**
```json
{
  "job_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "status": "processing",
  "progress": 45,
  "download_url": null
}

```


* **Response Sample (Completed):**
```json
{
  "job_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "status": "completed",
  "progress": 100,
  "download_url": "https://yourdomain.com/api/v1/downloads/a0eebc99....xlsx",
  "result_meta": {
    "detail": "",
    "failed_counter": 0
  }
}

```



---

## 4. Concurrency Safety & Background Workers

* **Background Processing:** Utilize Python Celery workers running independently from the main FastAPI web server, backed by a message broker (e.g., Redis or RabbitMQ).
* **Concurrency Safety:** Workers must safely compete for pending tasks using PostgreSQL row-level locking (`FOR UPDATE SKIP LOCKED`) to prevent race conditions or duplicate execution:
```sql
UPDATE jobs 
SET status = 'processing', updated_at = NOW() 
WHERE id = (
    SELECT id FROM jobs 
    WHERE status = 'pending' 
    ORDER BY created_at ASC 
    FOR UPDATE SKIP LOCKED 
    LIMIT 1
) 
RETURNING *;

```

## 5. Timeout, Error, and Memory Management

* **Timeout Handling:** When a worker picks up a task, initialize `timeout_at` (e.g., `NOW() + INTERVAL '15 minutes'`). A background heartbeat/cron monitor should catch stalled jobs:
```sql
UPDATE jobs 
SET status = 'failed', error_message = 'Task timeout exceeded', updated_at = NOW()
WHERE status = 'processing' AND timeout_at < NOW();

```

* **Memory Optimization:** Use memory-efficient streaming readers/writers (e.g., `openpyxl` with `write_only=True` in Python) to prevent RAM exhaustion when handling large Excel files.

---

## 6. Resource Lifecycle & Maintenance

* **Temporary Files Cleanup:** Implement a scheduled cleanup cron job to purge temporary upload/export files older than 24 hours (or immediately after confirmed client download).
* **Cache TTL:** Configure short Time-To-Live (TTL) policies (e.g., 1 hour post-completion) for any Redis/cache progress state keys.

---

## 7. High-Level Workflow Summary

```text
[Client] 
    │ 
    ├── 1. POST /jobs (Upload file / send parameters) ──> [Web Server] ──> [DB: Insert 'pending'] 
    │                                                                             │
    │ <── 2. Returns 202 Accepted + job_id <──────────────────────────────────────┘
    │
    ├── 3. GET /jobs/{id} (Polling every 3s) ──> [Web Server] ──> [Fetch Status from DB]
    │                                                                             │
    │ <── 4. Returns status (processing / completed + download link) <────────────┘
    │
[Background Worker] ──(Uses FOR UPDATE SKIP LOCKED)──> [Fetch Pending Job] 
    ├── Process Excel file (Streaming chunks)
    ├── Update progress metrics in DB (e.g., 25%, 50%, 75%)
    ├── Completion: Save results to DB/Storage & clear temp files/cache
    └── Update Status = 'completed' / 'failed'

```

# Management Tools Web Platform

Modern, distributed web application Built with **FastAPI**, **React + Vite + Tailwind CSS**, **PostgreSQL**, **Redis**, and **Celery**.

---

## Architecture Highlights

- **Clean Architecture & MVVM**: Decoupled React frontend (Model-View-ViewModel) and FastAPI backend (Service-Repository pattern).
- **Asynchronous Long-Running Task Pipeline**:
  - Non-blocking Excel import & export powered by Celery workers and Redis broker.
  - Concurrency safety with PostgreSQL row-level locking (`FOR UPDATE SKIP LOCKED`).
  - Real-time progress updates via WebSockets with automatic 3-second polling fallback.
- **Memory Optimized**: Chunked streaming reading and writing (`openpyxl` with `read_only=True` and `write_only=True`).
- **Database Abstraction**: PostgreSQL primary with dialect-agnostic models compatible with Microsoft SQL Server.
- **Watchdog & Automated Cleanup**: Celery Beat scheduled heartbeat monitor catching stalled tasks (`timeout_at < NOW()`) and purging temp files older than 24 hours.

---

## Directory Structure

```text
TPNV_RPT_TOOLS/
├── docker/                 # Docker Compose & Dockerfiles
├── backend/                # FastAPI application, SQLAlchemy models, Celery tasks
├── frontend/               # React 18, Vite, Tailwind CSS, ViewModels, Views
├── storage/                # Templates, uploads, and exported report files
├── run.ps1                 # Convenience launcher script (PowerShell)
├── README.md        # Importance Info
└── .env                    # Environment settings
```

---

## Quick Start

### 1. Launch with Docker Compose
Run in PowerShell:
```powershell
.\run.ps1 [...]
```
*(or standard command: `docker compose -f docker/docker-compose.yml up --build -d`)*

### 2. Access the Application
- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Default Login Credentials
- **Username:** `admin`
- **Password:** `admin`

---

# Hướng dẫn sử dụng [run.ps1]

#### 🚀 Chế độ Dev (Mặc định - Chạy script trực tiếp với reload):
```powershell
# Khởi động (tự động đảm bảo Postgres đã chạy)
.\run.ps1 up -Mode dev

# Rebuild dev container
.\run.ps1 build -Mode dev
```

#### 📦 Chế độ Release (Dùng Nuitka backend + npm bundle frontend):
```powershell
# Build toàn bộ bundle và biên dịch Nuitka
.\run.ps1 build -Mode release

# Khởi chạy bản Release
.\run.ps1 up -Mode release
```

#### 🛑 Dừng container:
```powershell
# Dừng application stack (PostgreSQL vẫn tiếp tục chạy)
.\run.ps1 down

# Dừng tất cả (bao gồm cả PostgreSQL container - dữ liệu trong storage/postgres_data vẫn an toàn)
.\run.ps1 down -All
```

#### 🐘 Quản lý riêng PostgreSQL:
```powershell
.\run.ps1 postgres up
.\run.ps1 postgres down
.\run.ps1 postgres restart
.\run.ps1 postgres logs
```

#### 🌐 Đường dẫn truy cập:
- **Web App (HTTPS)**: [https://localhost](https://localhost) *(hoặc [http://localhost](http://localhost) sẽ tự động redirect sang HTTPS)*
- **API Swagger Docs**: [https://localhost/docs](https://localhost/docs)

# DEPLOY

## Server Deployment (Standalone Export)
To build and package a completely standalone release bundle to deploy onto a target Linux/Windows server:
```powershell
.\run.ps1 export
```
The output zip archive in `dist/` contains all Docker images and deployment scripts (`deploy.sh` / `deploy.ps1`). On the server, run:
```bash
./deploy.sh load
./deploy.sh up
```

---

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
1. **PostgreSQL Persistence Stack (`docker-compose.postgres.prod.yml`)**:
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
2. Khởi động PostgreSQL stack (`docker-compose.postgres.prod.yml`).
3. Khởi động Application stack (`docker-compose.prod.yml`).
4. Backend tự động kiểm tra và tạo bảng database (`Base.metadata.create_all`) nếu chưa tồn tại.
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

# WSL2 : BAỎ vỆ SRC

Để bảo vệ file `.env` , docker

---

### Nguyên tắc cốt lõi cần nhớ

* **Windows Host (Dùng chung):** Nơi người khác có thể sử dụng hàng ngày, nhưng 
	**không được phép** có quyền truy cập vào không gian lưu trữ bên trong WSL2 của bạn.
* **WSL2 Ubuntu (Riêng tư):** Nơi chứa toàn bộ mã nguồn dự án, file `.env`,
	và Docker daemon của bạn. Chỉ có tài khoản Linux của bạn mới có quyền đọc/ghi.

---

### Các bước thực hiện chi tiết:
#### Bước 1: Di chuyển toàn bộ thư mục dự án vào bên trong WSL2
**chuyển toàn bộ thư mục dự án vào phân vùng Linux của WSL2** (ví dụ: `/home/ten_user_cua_ban/omc_project`).

#### Bước 2: Siết chặt quyền hạn (File Permissions) cho file `.env`
1. Mở WSL2 và trỏ đến thư mục dự án.
2. Chạy lệnh phân quyền nghiêm ngặt nhất cho file `.env`:
```bash
chmod 600 .env

```
**chỉ chủ sở hữu (owner)** file mới có quyền **Đọc và Ghi (`read/write`)**
3. Kiểm tra lại quyền:
```bash
ls -l .env

```
hiển thị dạng: `-rw-------` (chỉ `r` và `w` ở nhóm đầu tiên dành cho bạn, các nhóm sau là dấu `-`).

#### Bước 3: Bảo vệ tài khoản WSL2 và Root
1. **Đặt mật khẩu cho user Linux của bạn**.
2. **Đặt mật khẩu riêng cho tài khoản `root**` bên trong WSL bằng lệnh:
```bash
sudo passwd root

```

######


### 1. Cơ chế hoạt động khi cài Docker trực tiếp trên WSL2 Ubuntu

* **Không cần Docker Desktop:** Bạn có thể tắt hoặc gỡ hoàn toàn Docker Desktop khỏi Windows.
* **Docker Daemon chạy ngầm trong Linux:** Tiến trình quản lý container (`dockerd`) sẽ chạy trực tiếp bên trong nhân Linux của WSL2.
* **Socket nội bộ:** Các lệnh như `docker ps` hay `docker compose` sẽ giao tiếp qua socket cục bộ (`/var/run/docker.sock`) của riêng Linux, cực kỳ mượt mà và không bị ảnh hưởng bởi các thiết lập chia sẻ ổ đĩa rườm rà của Windows.

---

### 2. Ưu điểm lớn nhất của cách này

1. **Bảo mật tuyệt đối (Đúng với mục đích của bạn):**
* Toàn bộ mã nguồn, container, image, file `.env` và Docker socket đều nằm gọn trong không gian Linux của WSL2.
* Người dùng chung tài khoản Windows bên ngoài **hoàn toàn không thể** chạm tới Docker hay đọc file `.env` nếu không vượt qua được mật khẩu Linux/WSL2 của bạn.


2. **Hiệu suất cao hơn:** Tránh được lớp dịch vụ trung gian (proxy) mà Docker Desktop dùng để chuyển tiếp từ Windows sang WSL2, giúp tốc độ I/O ổ cứng và mạng của container nhanh hơn đáng kể.
3. **Môi trường chuẩn Linux:** Mọi thao tác, cấu hình, đường dẫn volume đều chuẩn 100% như khi bạn deploy lên một máy chủ Linux thực thụ (VPS, Cloud Server).

---

### 3. Nhược điểm cần lưu ý

* **Không có giao diện GUI:** Quản lý bằng dòng lệnh (CLI) (hoặc dùng các extension quản lý Docker trên VS Code trỏ vào WSL2).
* **Cổng mạng (Port Forwarding):** Như đã đề cập ở các phần trước,
nếu muốn các máy khác trong cùng mạng LAN truy cập vào web app chạy trong WSL2 này,
cần cấu hình port proxy một chút từ phía Windows sang WSL2.

---


######

Thiết lập **Port Proxy** từ Windows sang WSL2.
Dưới đây là hướng dẫn chi tiết từng bước bằng PowerShell (chạy với quyền Administrator):

---

### Bước 1: Lấy địa chỉ IP hiện tại của WSL2 Ubuntu
Mở một cửa sổ PowerShell (hoặc Terminal) bất kỳ và chạy lệnh sau để lấy IP nội bộ của WSL2:

```powershell
$wsl_ip = (wsl.exe -d Ubuntu -e hostname -I).Trim()
Write-Host "IP của WSL2 hiện tại là: $wsl_ip"

```

*(Lưu ý: Nếu phân phối Ubuntu có tên khác, hãy thay chữ `Ubuntu` bằng tên phân phối,
hoặc bạn có thể gõ `wsl hostname -I` bên trong terminal của Ubuntu).*

---

### Bước 2: Thiết lập Port Proxy trên Windows
Windows cần biết rằng: *Khi có bất kỳ kết nối nào gửi vào cổng X của máy Windows, hãy chuyển tiếp (forward) nó vào đúng cổng X của địa chỉ IP WSL2 vừa tìm được ở Bước 1.*

Mở **PowerShell với quyền Administrator** chạy đoạn script sau (nhớ thay đổi số cổng `8080` thành cổng web thực tế):

```powershell
# 1. Cấu hình cổng web (Ví dụ: 8080)
$port = 8080

# 2. Lấy tự động IP của WSL2
$wsl_ip = (wsl.exe -d Ubuntu -e hostname -I).Trim().Split(" ")[0]
Write-Host "Đang ánh xạ cổng $port tới WSL2 IP: $wsl_ip"

# 3. Xóa luật cũ nếu đã tồn tại (để tránh lỗi trùng lặp)
netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null

# 4. Thêm luật Port Proxy mới từ mọi địa chỉ mạng (0.0.0.0) trên Windows sang WSL2
netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wsl_ip

Write-Host "Cấu hình thành công!"

```

---

### Bước 3: Mở tường lửa Windows (Windows Firewall)
Dù đã cấu hình Port Proxy, nhưng nếu Windows Firewall bật,
nó có thể chặn các máy khác trong LAN truy cập vào. Bạn cần mở cổng trên Firewall:

Chạy tiếp lệnh sau trong **PowerShell (Admin)** (thay `8080` bằng cổng thưc tế):

```powershell
$port = 8080
New-NetFirewallRule -DisplayName "Docker-WSL2-Port-$port" -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow

```

---

### Bước 4: Kiểm tra kết quả

1. **Kiểm tra danh sách Port Proxy hiện tại trên Windows:**
```powershell
netsh interface portproxy show v4tov4

```
hiển thị cổng lắng nghe `8080` trên Windows đang trỏ đến IP của WSL2.
2. **Truy cập thử nghiệm:**
* Từ máy Windows host: Mở trình duyệt và gõ `http://localhost:8080` hoặc `[http://127.0.0.1:8080](http://127.0.0.1:8080)`.
* Từ máy tính khác trong mạng LAN: Lấy IP của máy Windows Server (ví dụ: `192.168.1.50`)
và truy cập `[http://192.168.1.50:8080](http://192.168.1.50:8080)`.

---

### ⚠️ Lưu ý quan trọng về IP của WSL2:
Mỗi khi **khởi động lại máy tính** hoặc khởi động lại hoàn toàn WSL2 (`wsl --shutdown`), địa chỉ IP của WSL2 (`$wsl_ip`) có thể sẽ thay đổi thành một IP mới.
Để không phải cấu hình lại thủ công mỗi lần bật máy, 
có thể đưa đoạn script tự động lấy IP và gán lại `netsh interface portproxy` vào một file script PowerShell
chạy tự động khi Windows khởi động, hoặc cấu hình IP tĩnh cho WSL2 nếu cần thiết.