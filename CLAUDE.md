# WorkMate 项目说明

## 项目定位
企业 AI 助手。Web 界面 + 飞书机器人双入口，LLM 编排由 Dify 负责，本系统负责界面、会话管理、工具暴露（MCP）、数据源接入。

## 技术栈
- **前端**：Vue 3 + TypeScript + Element Plus + Pinia，位于 `frontend/`
- **后端**：FastAPI + SQLAlchemy async + SQLite/MySQL，用 uv 管理，位于 `backend/`

## 架构
```
用户(Web/飞书)
      ↓
WorkMate 后端 (FastAPI, port 8000)
      ↓ 调用 Dify Chatflow API (SSE流)
    Dify (LLM编排，判断走哪个分支)
      ↓ MCP调用 → /mcp endpoint
WorkMate MCP Server (暴露工具给Dify)
      ↓
企业数据源 (ERP/共享/...)
```

## 启动方式
```bash
# 后端
cd backend
uv run uvicorn app.main:app --reload   # → http://localhost:8000
# 测试账号: admin/admin123, test001/test123

# 前端
cd frontend
npm run dev   # → http://localhost:5173
```

## 关键配置（backend/.env）
```
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=<填入Dify API Key>
SECRET_KEY=<改为随机长字符串>
DATABASE_URL=sqlite+aiosqlite:///./workmate.db
```

## Phase 1 已完成
- [x] JWT 登录认证（工号+密码）
- [x] 会话 CRUD API
- [x] Dify 流式 Chat API（SSE）
- [x] MCP Server 基础框架（`/mcp` endpoint）
- [x] 前端：登录页、对话界面（侧边栏+消息流+功能选择器）

## Phase 2 已完成
- [x] Skills 动态加载系统（上传 .zip → uv pip install → importlib 热加载 → 注册到 MCP）
- [x] 飞书消息回调接口（`/api/v1/feishu/callback`，支持 URL 验证 + im.message.receive_v1）
- [x] 多数据源配置管理（datasources 表 + CRUD + 连接测试，支持 mysql/pg/mssql/sqlite/http_api/shared）
- [x] 聊天记录工具调用展示（agent_thought 事件 → SSE tool_call → 前端可折叠 ToolCall 卡片）
- [x] 管理页面（`/admin`，三 Tab：用户管理 / Skills 安装 / 数据源配置，is_admin 权限控制）

## 目录结构关键文件
```
backend/app/
├── main.py              # FastAPI 入口，挂载 /mcp
├── config.py            # pydantic-settings，读 .env
├── database.py          # SQLAlchemy async 引擎
├── models/              # ORM: User, Conversation, Message, Skill
├── api/v1/
│   ├── auth.py          # POST /auth/login, /auth/refresh, GET /auth/me
│   ├── conversations.py # CRUD 会话
│   ├── chat.py          # POST /chat/stream (SSE → Dify)
│   └── skills.py        # GET /skills (stub)
├── core/
│   ├── security.py      # bcrypt + PyJWT
│   └── deps.py          # get_current_user 依赖
├── services/dify.py     # Dify httpx 异步客户端
└── mcp/
    ├── server.py        # FastMCP，get_mcp_app() 挂载到 FastAPI
    ├── registry.py      # 工具注册表（register/unregister/get_all）
    └── tools/base.py    # ToolBase ABC 接口

frontend/src/
├── stores/              # auth.ts, conversations.ts
├── api/                 # request.ts(axios), auth.ts, conversations.ts, chat.ts(fetch SSE)
├── components/
│   ├── AppSidebar.vue   # 左侧会话列表
│   ├── ChatPanel.vue    # 右侧对话主体
│   ├── MessageItem.vue  # Markdown 渲染
│   ├── FunctionSelector.vue  # 功能下拉
│   └── MessageInput.vue
└── views/
    ├── LoginView.vue
    └── ChatView.vue
```

## 功能选择器与 Dify 的交互
- 用户选择功能（周报/ERP/共享）→ 作为 `inputs.function` 传入 Dify
- 未选择时 → Dify LLM 自行判断走哪个分支
- 配置项：`DIFY_CONVERSATION_VAR_FUNCTION`（默认值 `"function"`）

## Skills 系统设计意图（Phase 2）
- 每个 Skill 是标准 Python 包，实现 `ToolBase` 接口（`app/mcp/tools/base.py`）
- 上传包 → `uv pip install` 依赖 → `importlib` 热加载 → 注册到 `mcp/registry.py`
- 注册后 MCP Server 自动暴露新工具给 Dify
