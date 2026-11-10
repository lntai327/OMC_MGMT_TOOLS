# TODO

Megawan
- trong file đầu vào chị gán sẵn UPE nhưng nếu e làm data theo file csht_upe có gì c chủ động thêm/xoá/sửa theo nguyên tắc ation là insert/delete -> đã thực hiện
- Megawan à, chị làm gì thì cứ để đó đi,
khi nào xong yêu cầu cũ -> thì e đọc yêu cầu mới rồi hỏi sau

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

# make cer:
mkdir certs
cd certs
mkcert -cert-file cert.pem -key-file key.pem localhost 127.0.0.1 ::1 192.168.1.200 10.53.67.140

# 1. Chuyển mạng Wi-Fi sang chế độ Private
## Get-NetConnectionProfile
Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private

# 2. Mở Port 80 và 443 trên Windows Firewall
## Get-NetFirewallPortFilter | Where-Object { $_.LocalPort -eq "80" -or $_.LocalPort -eq "443" } | Get-NetFirewallRule
New-NetFirewallRule -DisplayName "OMC Web HTTP (80)" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "OMC Web HTTPS (443)" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow

# Cho phép lưu lượng Inbound qua lớp tường lửa Hyper-V của WSL
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow

[wsl2]
networkingMode=mirrored
firewall=false
[experimental]
hostAddressLoopback=true