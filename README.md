# 📚 AI 知识库问答系统

基于 Django + React 的智能知识库问答应用，支持上传文档（PDF/Word/TXT/Markdown），通过 RAG（检索增强生成）技术实现基于文档内容的智能问答。

## 技术架构

```
┌──────────┐     HTTP/SSE     ┌──────────────┐     OpenAI SDK     ┌─────────────┐
│  React   │ ◄──────────────► │  Django DRF   │ ◄───────────────► │  硅基流动    │
│  前端    │                  │  后端 API     │                   │  DeepSeek-V3 │
└──────────┘                  └──────┬───────┘                   └─────────────┘
                                     │
                              ┌──────▼───────┐
                              │   ChromaDB    │
                              │   向量存储     │
                              └──────────────┘
```

| 层 | 技术 |
|---|------|
| 后端 | Django 6.0 + DRF + JWT |
| 前端 | React 19 + Vite + TailwindCSS |
| 向量库 | ChromaDB |
| LLM | DeepSeek-V3 (硅基流动) |
| Embedding | BAAI/bge-large-zh-v1.5 |

## 功能

- 🔐 用户注册/登录（JWT 认证）
- 📁 知识库管理（CRUD）
- 📄 文档上传与自动解析（PDF/Word/TXT/Markdown）
- 🔍 智能检索（语义搜索 + 段落分块）
- 💬 流式对话（SSE）— 打字机效果
- 📖 答案溯源 — 展示答案引用的原文片段
- 🐳 Docker 一键部署

## RAG Pipeline

1. **上传** → 文档保存到 Django
2. **解析** → PyPDF2/python-docx 提取纯文本
3. **分块** → RecursiveCharacterTextSplitter (500 chars, 50 overlap)
4. **向量化** → 硅基流动 Embedding API
5. **存储** → ChromaDB (每知识库独立 Collection)
6. **检索** → 用户提问 → Embedding → ChromaDB top-5 → 拼接上下文
7. **生成** → DeepSeek-V3 流式返回，标注引用来源

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件：

```env
SILICONFLOW_API_KEY=your_key_here
SECRET_KEY=your_django_secret
DEBUG=True
```

### 2. 启动后端

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/

### Docker 部署

```bash
SILICONFLOW_API_KEY=your_key docker compose up -d
```

## API 文档

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/` | 注册 |
| POST | `/api/auth/login/` | 登录（返回 JWT） |
| GET | `/api/auth/me/` | 当前用户信息 |
| GET/POST | `/api/knowledge-bases/` | 知识库列表/创建 |
| GET/PUT/DELETE | `/api/knowledge-bases/:id/` | 知识库详情 |
| GET/POST | `/api/knowledge-bases/:id/documents/` | 文档列表/上传 |
| DELETE | `/api/documents/:id/` | 删除文档 |
| GET/POST | `/api/knowledge-bases/:id/conversations/` | 对话列表/创建 |
| GET/DELETE | `/api/conversations/:id/` | 对话详情 |
| GET | `/api/conversations/:id/messages/` | 消息列表 |
| POST | `/api/knowledge-bases/:id/chat/` | 新建对话+SSE流式回答 |
| POST | `/api/conversations/:id/chat/` | 继续对话+SSE流式回答 |

## 项目结构

```
django/
├── config/                 # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/           # 用户认证
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   └── knowledge/          # 知识库核心
│       ├── models.py       # KnowledgeBase, Document, Conversation, Message
│       ├── serializers.py
│       ├── views.py        # REST API + Chat
│       ├── urls.py
│       └── rag/            # RAG 引擎
│           ├── __init__.py # LLM client
│           ├── engine.py   # 解析/分块/向量化/存储/检索
│           └── chat.py     # SSE 流式对话
├── frontend/               # React 前端
│   ├── src/
│   │   ├── api/client.js   # API 封装
│   │   ├── context/        # Auth Context
│   │   ├── pages/          # Login, Dashboard, Chat
│   │   └── App.jsx         # 路由
│   └── vite.config.js
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

## Demo 演示要点

1. 注册 → 创建知识库 → 上传 PDF
2. 进入对话 → 提问 → 观察流式打字机回复
3. 展开来源引用 → 验证答案基于原文
4. 多轮对话 → 展示上下文记忆

## 面试亮点

- **Django 核心**：Models(ORM)、DRF Serializers、JWT Auth、Class-based Views
- **RAG 工程**：文档解析 → 语义分块 → 向量检索 → LLM 生成
- **流式架构**：SSE (Server-Sent Events) — 后端 StreamingHttpResponse → 前端 ReadableStream
- **工程实践**：用户数据隔离、异步文档处理、Docker 部署
