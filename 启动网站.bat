@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==============================================
echo  NeuroSearch 本地网站
echo  目录：%CD%
echo ==============================================

set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY ( where py >nul 2>&1 && set "PY=py" )

if not defined PY (
  echo.
  echo 没找到 Python。请先安装 https://www.python.org/downloads/ 并勾选 Add to PATH
  echo.
  pause
  exit /b 1
)

if not exist "server\neurosearch.db" (
  echo 首次运行，正在生成数据库...
  %PY% server\seed.py
  if errorlevel 1 (
    echo 建库失败，请把上面的报错发给维护者。
    pause
    exit /b 1
  )
)

echo.
echo 地址：http://localhost:8000
echo 关闭网站：关掉这个窗口。
echo.
start "" http://localhost:8000
%PY% server\server.py
pause
