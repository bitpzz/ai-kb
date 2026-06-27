#!/bin/bash
# AI 知识库 — 一键启动
set -e
cd "$(dirname "$0")"

echo "=== 检查 Python 3.12 ==="
command -v python3.12 >/dev/null || dnf install -y python3.12 python3.12-pip

echo "=== 安装依赖 ==="
pip3.12 install -r requirements.txt pysqlite3-binary

echo "=== 数据库迁移 ==="
python3.12 manage.py migrate

echo "=== 创建 .env ==="
[ -f .env ] || cat > .env << 'EOF'
SILICONFLOW_API_KEY=你的KEY
SECRET_KEY=随机字符串
DEBUG=False
ALLOWED_HOSTS=82.156.164.62,localhost,127.0.0.1
EOF

echo "=== 启动后端 (8000) ==="
nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 > /tmp/gunicorn.log 2>&1 &
echo "后端 PID: $!"

echo "=== 启动代理 (8080) ==="
nohup python3.12 proxy.py 8080 > /tmp/proxy.log 2>&1 &
echo "代理 PID: $!"

echo ""
echo "✅ 启动完成！"
echo "访问: http://\$(hostname -I | awk '{print \$1}'):8080/kb/"
