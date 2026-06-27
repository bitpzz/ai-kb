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
SILICONFLOW_API_KEY=把你的API_KEY放这里
SECRET_KEY=生成一个随机字符串
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

## CI/CD 自动部署

本项目使用 GitHub Actions 自动部署到服务器。

### 工作流文件
`.github/workflows/deploy.yml`

### 流程
1. `git push` 到 `main` 分支
2. GitHub Actions 自动触发
3. 构建 Docker 镜像（前端 + 后端）
4. 推送到 GitHub Container Registry (ghcr.io)
5. SSH 到服务器，拉取最新镜像并重启

### 必需的 GitHub Secrets

| Secret | 说明 |
|--------|------|
| `SERVER_HOST` | 服务器 IP，如 82.156.164.62 |
| `SERVER_USER` | SSH 用户名，如 root |
| `SERVER_PASSWORD` | SSH 密码 |
| `SILICONFLOW_API_KEY` | 硅基流动 API key |
| `DJANGO_SECRET_KEY` | Django 密钥（随机字符串） |

### 服务器首次初始化

```bash
ssh root@your-server
mkdir -p /opt/ai-kb
cd /opt/ai-kb
# 复制项目中的 docker-compose.yml 到此目录
# 之后每次 git push 会自动拉取最新镜像
```
