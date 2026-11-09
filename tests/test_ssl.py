#nuitka --standalone --onefile test_ssl.py

import sys
import urllib.request

print("--- ĐANG KIỂM TRA KẾT NỐI SSL ---")

# 1. Thử kích hoạt truststore (nếu bạn chọn giải pháp dùng chứng chỉ hệ điều hành)
# try:
#   import truststore

#   truststore.inject_into_ssl()
#   print("[OK] Đã inject thành công thư viện 'truststore'.")
# except ImportError:
#   print(
#       "[INFO] Không sử dụng 'truststore' (hoặc chưa cài đặt), dùng cơ chế"
#       " mặc định/certifi."
#   )

# 2. Thực hiện gọi request HTTPS thực tế tới một API công khai phổ biến
url = "https://api.github.com"
print(f"Đang gửi request kết nối tới: {url} ...")

try:
  # Cần thêm User-Agent vì GitHub yêu cầu
  req = urllib.request.Request(url, headers={"User-Agent": "TestSSLScript/1.0"})
  with urllib.request.urlopen(req, timeout=10) as response:
    status_code = response.getcode()
    print(f"\n✅ THÀNH CÔNG! Kết nối HTTPS thành công (Status Code: {status_code})")
    print("Lỗi SSL đã được khắc phục hoàn toàn trên môi trường đóng gói.")
except Exception as e:
  print(f"\n❌ THẤT BẠI! Vẫn gặp lỗi SSL hoặc lỗi mạng:")
  print(f"Chi tiết lỗi: {e}")
  sys.exit(1)

# Giữ cửa sổ console lại để đọc kết quả nếu chạy file .exe trực tiếp trên Windows
if getattr(sys, "frozen", False):
  input("\nNhấn Enter để thoát...")