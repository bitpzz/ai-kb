#!/bin/bash
# pack.sh — 本地打包脚本
# 用法: bash pack.sh
# 输出: /tmp/ai-kb-deploy.tar.gz

set -e
cd "$(dirname "$0")"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="/tmp/ai-kb-$TIMESTAMP.tar.gz"

echo "=== 打包项目（排除开发环境文件）==="
tar -czf "$OUTPUT" \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/dist' \
  --exclude='chroma_data' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='db.sqlite3' \
  --exclude='media' \
  --exclude='*.log' \
  .

echo ""
echo "✅ 打包完成: $OUTPUT"
echo "   上传到服务器: scp $OUTPUT root@82.156.164.62:/tmp/"
