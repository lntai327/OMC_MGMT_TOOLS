# TODO

Megawan
- sửa lỗi thời gian DB k theo múi giờ : last_update, created_at, updated_at
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

# RELEASE

## release Desktop:
nuitka --standalone --windows-console-mode=disable --windows-icon-from-ico=.\src\rs\cfg\rpt_icon.ico --include-windows-runtime-dlls=yes --include-data-dir=.\src\rs\cfg=rs\cfg --include-data-dir=.\src\rs\rpt=rs\rpt --include-data-dir=.\src\rs\font=rs\font --include-package=flet --include-package-data=flet --output-dir=dist --output-filename=OMC_QNN_Report_Tool_v1.0.4.1_t4.exe .\src\main.py

force / disable / attach / hide

## web
docker compose --env-file .env -f .\docker\docker-compose.release.yml down
docker compose --env-file .env -f .\docker\docker-compose.release.yml build frontend
docker compose --env-file .env -f .\docker\docker-compose.release.yml up -d --force-recreate

## version naming
v1.1.1 = vBigUpdate.NumberReportType.Minor

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

# docker
##
docker network create "omc_network" | Out-Null
docker build -f .\docker\postgres.Dockerfile -t omc-postgres:latest .
docker compose --env-file .env -f .\docker\docker-compose.postgres.prod.yml up -d

docker compose -f .\docker\docker-compose.release.yml build
docker compose --env-file .env -f .\docker\docker-compose.prod.yml up -d

##
### Frontend
docker compose --env-file .env -f .\docker\docker-compose.release.yml up -d --no-deps --build frontend
### Chỉ thay đổi code API/Web Backend
docker compose --env-file .env -f .\docker\docker-compose.release.yml up -d --no-deps --build backend
### Thay đổi logic Task ngầm / Worker (Import, Export, Watchdog, Beat):
(backend, celery_worker và celery_beat dùng chung Docker image (omc_mgmt_tool-backend:release).
Do đó build 1 lần và áp dụng cho các container liên quan:)
1. Build lại image backend
docker compose --env-file .env -f .\docker\docker-compose.release.yml build backend
2. Cập nhật lại các container backend & worker (không ảnh hưởng frontend, redis, db)
docker compose --env-file .env -f .\docker\docker-compose.release.yml up -d --no-deps backend celery_worker celery_beat

##
docker compose -f docker/docker-compose.yml logs -f celery_worker

docker logs backend --tail 20