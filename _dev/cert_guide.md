# tao cert
mkcert -install
mkdir certs
cd certs
mkcert -cert-file cert.pem -key-file key.pem localhost 127.0.0.1 ::1 192.168.88.165


# Cài đặt trên các thiết bị khác trong mạng LAN (Điện thoại, Laptop khác)

Các thiết bị khác trong mạng nội bộ chưa biết đến Root CA bạn vừa tạo ở Bước 2 nên vẫn sẽ báo lỗi bảo mật khi truy cập https://192.168.88.165. Để khắc phục:
1. Chạy lệnh sau trên máy tạo chứng chỉ để tìm vị trí file rootCA.pem:bash
mkcert -CAROOT
Use code with caution.
2. Copy file rootCA.pem trong thư mục đó gửi sang điện thoại hoặc máy tính khác (Lưu ý: Tuyệt đối chỉ gửi file rootCA.pem, không bao giờ gửi file rootCA-key.pem).
3. Cài đặt file rootCA.pem lên thiết bị nhận:
	• Windows khác: Đổi tên thành rootCA.crt -> Click đúp -> Install Certificate -> Chọn Local Machine -> Chọn Place all certificates in the following store -> Browse chọn Trusted Root Certification Authorities.
	• iPhone / iPad: Gửi file qua AirDrop/Zalo/Email -> Bấm vào để tải hồ sơ về -> Vào Cài đặt (Settings) > Đã tải về hồ sơ (Profile Downloaded) để cài đặt -> Sau đó vào Cài đặt chung > Giới thiệu > Cài đặt tin cậy chứng nhận (Certificate Trust Settings) và gạt bật tin cậy cho chứng chỉ mkcert.
	• Android: Vào Cài đặt > Bảo mật > Mã hóa & thông tin xác thực > Cài đặt chứng chỉ > Chứng chỉ CA và chọn file rootCA.pem.