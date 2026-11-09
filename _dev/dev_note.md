# TODO
1. Qly Hsuat Xgspon: Tiếp tục thực hiện/hoàn thiên các tính năng:
- thêm thông tin cho bản ghi : loại card combo, sfp combo, (...)
- sửa logic update bản ghi (không cập nhật nếu không có gì thay đổi)
- (...)

2. Thực hiện chương trình quản lý ODF , Sợi quang
3. (Khác)

#
py -3.13 --version
## 1. Cài đặt trình tạo môi trường ảo (nếu chưa có)
sudo apt install python3-venv -y
## 2. Tạo một thư mục cho dự án và đi vào đó
mkdir my_ocr_project && cd my_ocr_project
## 3. Tạo môi trường ảo tên là 'venv'
py -3.13 -m venv .venv #Python 3.13.11
## 4. Kích hoạt môi trường ảo
source venv/bin/activate #linux
.venv\Scripts\activate #win
## 5. Bây giờ bạn có thể dùng pip thoải mái
pip install pytesseract pdf2image Pillow
## Exit
deactivate

#
pip freeze > requirements.txt
pip install -r requirements.txt

#release note:
nuitka --standalone --windows-console-mode=disable --windows-icon-from-ico=.\src\rs\cfg\rpt_icon.ico --include-windows-runtime-dlls=yes --include-data-dir=.\src\rs\cfg=rs\cfg --include-data-dir=.\src\rs\rpt=rs\rpt --include-package=flet --include-package-data=flet --output-dir=dist --output-filename=OMC_QNN_Report_Tool_id1_v1.0.4.1.exe .\src\main.py

force / disable / attach / hide

#version naming
v1.1.1.1 = v1.BigUpdate.NumberReportType.Minor