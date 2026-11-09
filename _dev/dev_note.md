# TODO

HS PON:
- Format HS_SD_XGSPON : căn giữa chữ MPM
- tách 3 file
- "Tất cả site" : xuất ra cả 3 (Đông, Tây, 2 site)
- thêm tìm "Tất cả" cho các trường : Tên hệ thống, IP, TTVT, Phường xã
Vd: chọn tìm "Tất cả", ký tự tìm: "a", thì sẽ tìm trên các trường "Tên hệ thống, IP, TTVT, Phường xã" có ký tự "a"
- export theo option checkbox

BTS
- DS Cảnh báo : 1 trạm thì các mã lỗi dồn thành 1 dòng theo thứ tự: Không tìm thấy NE trên RIMS, FMS chưa có phân loại trạm hoặc NE chưa gán CSHT trên RIMS, FMS chưa có phân loại trạm

CELL
- remove 2G branch Stable

Megawan
- complete each feature
- chuyển sang web base
- hoàn thiện chi tiết

Release DB note:


#
py -3.13 --version
## 1. Cài đặt trình tạo môi trường ảo (nếu chưa có)
sudo apt install python3-venv -y
## 2. Tạo một thư mục cho dự án và đi vào
mkdir my_ocr_project && cd my_ocr_project
## 3. Tạo môi trường ảo tên là 'venv'
py -3.13 -m venv .venv #Python 3.13.11
## 4. Kích hoạt môi trường ảo
source venv/bin/activate #linux
.venv\Scripts\activate #win
## 5. pip
pip install pytesseract pdf2image Pillow
## Exit
deactivate

#
pip freeze > requirements.txt
pip install -r requirements.txt

#release note:
nuitka --standalone --windows-console-mode=disable --windows-icon-from-ico=.\src\rs\cfg\rpt_icon.ico --include-windows-runtime-dlls=yes --include-data-dir=.\src\rs\cfg=rs\cfg --include-data-dir=.\src\rs\rpt=rs\rpt --include-data-dir=.\src\rs\font=rs\font --include-package=flet --include-package-data=flet --output-dir=dist --output-filename=OMC_QNN_Report_Tool_v1.0.4.1_t4.exe .\src\main.py

force / disable / attach / hide

#version naming
v1.1.1.1 = v1.BigUpdate.NumberReportType.Minor

# GIT
git ls-files | grep login_page.py
git rm --cached src/frontend/pages/login_page.py

Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force   
Get-ChildItem -Path . -Recurse -File -Include "*.pyc","*.pyo" | Remove-Item -Force

# compact release
## obfuscate
pip install pyarmor
pyarmor gen main.py
pyarmor gen -r src/

## Delete comment
^\s*#.*\n? #removes full-line comments
#.* #Remove Inline Comments
run script

## build nuitka