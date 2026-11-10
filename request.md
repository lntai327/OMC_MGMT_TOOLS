# Request Refactor Docker Container:
## postgres
- Create another compose stack separate for postgres only
- setup volume mount to mount postgres data to host machine to persistence data not loss when remove container
## frontend
- use Nginx
- enable https : auto direct https, self-signed cer (gen mkcert storaged in /storage/certs)

# Request Refactor "run.ps1":
## must have option to switch dev and release mode
- dev : just copy script to container to run
- release : use result after build frontend(npm) and backend(nuitka) , not use raw script