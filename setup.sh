#!/bin/bash
# 首次部署：在服务器上执行一次
# 后续每次 git push 自动更新（通过 GitHub Actions docker compose build）

set -e

echo "=== 1. 安装 Docker ==="
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | bash
  systemctl start docker
  systemctl enable docker
fi

echo "=== 2. 克隆项目 ==="
cd /opt
test -d ai-kb || git clone https://github.com/bitpzz/ai-kb.git
cd ai-kb

echo "=== 3. 创建 .env ==="
test -f .env || cat > .env << 'EOF'
SILICONFLOW_API_KEY=你的KEY
SECRET_KEY=随机字符串
DEBUG=False
ALLOWED_HOSTS=82.156.164.62,localhost,127.0.0.1
EOF
echo "!!! 请编辑 /opt/ai-kb/.env 填入真实的 API Key 和随机 SECRET_KEY，然后重新运行此脚本"

echo "=== 4. 构建并启动 ==="
docker compose build
docker compose up -d

echo "=== 5. 确认状态 ==="
docker compose ps
echo ""
echo "✅ 部署完成！"
echo "然后在宝塔 Nginx 添加反向代理: /ai-kb/ → http://127.0.0.1:8080"
