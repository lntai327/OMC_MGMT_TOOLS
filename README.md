# VNPT TPNV OMC Report Tools Web Platform

Modern, distributed web application refactored from desktop Flet application for VNPT OMC. Built with **FastAPI**, **React + Vite + Tailwind CSS**, **PostgreSQL**, **Redis**, and **Celery**.

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
├── backend/                # FastAPI application, SQLAlchemy models, Celery tasks, Alembic
├── frontend/               # React 18, Vite, Tailwind CSS, ViewModels, Views
├── storage/                # Templates, uploads, and exported report files
├── run.ps1                 # Convenience launcher script (PowerShell)
├── TESTING_GUIDE.md        # Comprehensive manual testing guide
└── .env                    # Environment settings
```

---

## Quick Start

### 1. Launch with Docker Compose
Run in PowerShell:
```powershell
.\run.ps1 build
```
*(or standard command: `docker compose -f docker/docker-compose.yml up --build -d`)*

### 2. Access the Application
- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Default Login Credentials
- **Username:** `admin`
- **Password:** `demo`

---

## User Manual Testing Guide
Refer to [TESTING_GUIDE.md](TESTING_GUIDE.md) for step-by-step test cases covering health checks, authentication, Megawan CRUD, search filters, async Excel import/export progress, and worker/watchdog logs.
