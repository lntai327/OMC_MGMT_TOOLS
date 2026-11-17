Ran list model files
Analyzed user.py:L1-24

Khi muốn sửa đổi cấu trúc bảng cơ sở dữ liệu (thêm/xóa/sửa cột, đổi kiểu dữ liệu, thêm index...), quy trình chuẩn với **SQLAlchemy & Alembic** gồm **4 bước** như sau:

---

### Bước 1: Sửa Model trong code Python

Vào thư mục [backend/app/models/] và sửa class Model tương ứng.

*Ví dụ:* Muốn thêm cột `phone_number` vào bảng `users` trong file [user.py]:
```python
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    # ...
    # Thêm cột mới ở đây:
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

---

### Bước 2: Dùng Alembic tự động tạo file Migration mới (Autogenerate)

Chạy lệnh sau trong PowerShell để Alembic so sánh giữa **Model Python** và **Database PostgreSQL thực tế**, từ đó tự động sinh file migration:

```powershell
docker exec -it backend alembic revision --autogenerate -m "add_phone_number_to_users"
```

Alembic sẽ tạo ra một file mới trong thư mục [backend/alembic/versions/], ví dụ: `002_add_phone_number_to_users.py`.

---

### Bước 3: Kiểm tra lại file migration vừa sinh ra

Mở file mới trong [backend/alembic/versions/] để xem:
* Hàm **`upgrade()`**: Đã có lệnh `op.add_column(...)` chính xác chưa.
* Hàm **`downgrade()`**: Đã có lệnh `op.drop_column(...)` để hoàn tác khi cần chưa.

> [!TIP]
> Luôn nên mở file migration kiểm tra trước khi apply. Đối với trường hợp **đổi tên cột**, Alembic đôi khi hiểu nhầm là `drop_column` cột cũ và `add_column` cột mới (làm mất dữ liệu cũ của cột đó). Khi đó bạn chỉ cần sửa lại trong file thành `op.alter_column('users', 'old_name', new_column_name='new_name')`.

---

### Bước 4: Áp dụng thay đổi vào Database (Upgrade)

Chạy lệnh để thực thi migration vào PostgreSQL:

```powershell
docker exec -it backend alembic upgrade head
```

*(Hoặc khi bạn restart lại backend bằng `.\run.ps1 restart`, container cũng tự động chạy lệnh `alembic upgrade head` lúc khởi động).*

---

### Các lệnh hữu ích khác khi làm việc với Alembic:

| Thao tác | Lệnh |
| :--- | :--- |
| **Xem phiên bản hiện tại của DB** | `docker exec -it backend alembic current` |
| **Xem lịch sử các bản migration** | `docker exec -it backend alembic history` |
| **Hoàn tác 1 bước (Rollback)** | `docker exec -it backend alembic downgrade -1` |
| **Rollback về ban đầu (Xóa hết bảng)** | `docker exec -it backend alembic downgrade base` |