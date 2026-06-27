#!/bin/bash
# 首次部署：在服务器上执行一次
# 后续每次 git push 自动更新（通过 GitHub Actions）

set -e

echo "=== 1. 安装 Python 3.12 ==="
command -v python3.12 >/dev/null || dnf install -y python3.12 python3.12-pip 2>/dev/null || apt install -y python3.12 python3.12-pip 2>/dev/null || true

echo "=== 2. 安装 Node.js (for frontend build) ==="
command -v node >/dev/null || {
  curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
  apt install -y nodejs 2>/dev/null || dnf install -y nodejs 2>/dev/null || true
}

echo "=== 3. 克隆项目 ==="
cd /opt
test -d ai-kb || git clone https://github.com/bitpzz/ai-kb.git
cd ai-kb
git pull origin main

echo "=== 4. 创建 .env ==="
test -f .env || cat > .env << 'EOF'
SILICONFLOW_API_KEY=你的KEY
SECRET_KEY=随机字符串
DEBUG=False
ALLOWED_HOSTS=82.156.164.62,localhost,127.0.0.1
EOF
echo "!!! 请编辑 /opt/ai-kb/.env 填入真实的 API Key 和随机 SECRET_KEY"

echo "=== 5. 安装 Python 依赖 ==="
pip3.12 install -r requirements.txt

echo "=== 6. 数据库迁移 ==="
python3.12 manage.py migrate

echo "=== 7. 构建前端 ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 8. 启动后端 (8000) ==="
pkill -f gunicorn 2>/dev/null || true
sleep 1
nohup gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120 > /tmp/gunicorn.log 2>&1 &

sleep 2
pgrep -a gunicorn && echo "✅ 后端已启动" || echo "❌ 后端启动失败"

echo ""
echo "=== 部署完成 ==="
echo "然后在宝塔 Nginx 配置 /ai-kb/ 反向代理到 127.0.0.1:8080"
