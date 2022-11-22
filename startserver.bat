@ECHO OFF
start cmd.exe /C "..\venv\Scripts\python.exe manage.py runserver"
start "C:\Program Files\Mozilla Firefox\firefox.exe" "http://127.0.0.1:8000/"