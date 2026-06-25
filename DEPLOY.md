# ── 服务器部署 ────────────────────────────────────────────────

## 1. 上传项目到服务器

```bash
# 在本地执行（把 your-server-ip 换成你的服务器 IP）
rsync -avz \
  --exclude 'venv' \
  --exclude 'node_modules' \
  --exclude 'frontend/dist' \
  --exclude 'chroma_data' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'db.sqlite3' \
  --exclude '.DS_Store' \
  ./ root@<your-server-ip>:/opt/ai-kb/
```

## 2. 在服务器上操作

```bash
ssh root@<your-server-ip>
cd /opt/ai-kb
```

### 2.1 创建 .env

```bash
cat > .env << 'EOF'
SILICONFLOW_API_KEY=sk-your-api-key-here
SECRET_KEY=<生成一个随机字符串>
DEBUG=False
ALLOWED_HOSTS=<your-server-ip>
EOF
```

### 2.2 构建并启动

```bash
docker compose up -d --build
```

### 2.3 查看运行状态

```bash
docker compose ps
docker compose logs -f
```

## 3. 验证

```bash
# 注册用户
curl http://localhost/api/auth/register/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","email":"admin@example.com"}'

# 浏览器访问 http://<your-server-ip>
```

## 4. 常用运维命令

```bash
docker compose restart        # 重启
docker compose down           # 停止
docker compose up -d --build  # 重新构建并启动
docker compose logs backend   # 只看后端日志
docker compose exec backend python manage.py shell  # 进 Django shell
```
