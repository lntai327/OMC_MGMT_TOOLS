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



---

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