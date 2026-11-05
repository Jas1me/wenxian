#!/bin/bash
# NeuroSearch 本地启动器（macOS 双击运行）
# 作用：找到 Python 3 → 首次运行自动建库 → 启动本地服务 → 自动打开浏览器
cd "$(dirname "$0")" || exit 1

echo "=============================================="
echo " NeuroSearch 本地网站"
echo " 目录：$(pwd)"
echo "=============================================="

PY=""
for c in python3 python3.13 python3.12 python3.11 python3.10 python3.9 python; do
  if command -v "$c" >/dev/null 2>&1; then
    if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      PY="$c"; break
    fi
  fi
done

if [ -z "$PY" ]; then
  echo ""
  echo "✗ 没找到可用的 Python 3（需要 3.8 或更高）。"
  echo "  请先安装：https://www.python.org/downloads/macos/"
  echo "  装完关掉这个窗口，重新双击本文件。"
  echo ""
  read -r -p "按回车键关闭…" _
  exit 1
fi

echo "Python：$("$PY" --version 2>&1)  ($(command -v "$PY"))"

if [ ! -f "server/neurosearch.db" ]; then
  echo ""
  echo "首次运行，正在生成数据库（约 1 秒）…"
  if ! "$PY" server/seed.py; then
    echo "✗ 建库失败，请把上面的报错发给维护者。"
    read -r -p "按回车键关闭…" _
    exit 1
  fi
fi

PORT="${PORT:-8000}"
URL="http://localhost:$PORT"

echo ""
echo "地址：$URL"
echo "关闭网站：按 Control + C，或直接关掉这个窗口。"
echo ""

( sleep 2; open "$URL" ) &
PORT="$PORT" exec "$PY" server/server.py
