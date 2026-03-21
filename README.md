# Quackbase

CSV / XLSX 数据探索平台，支持多用户、权限管理、数据上传与导出。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 · Vite · Pinia · Vue Router |
| 后端 | Python · FastAPI · DuckDB · PyJWT |
| 部署 | Docker · Nginx |

## 目录结构

```
quackbase/
├── frontend-vue/         ← Vue 3 前端
│   ├── src/
│   ├── vite.config.js
│   ├── .env.development  # 本地开发配置
│   └── .env.production   # 生产部署配置
├── backend/              ← FastAPI 后端
│   ├── main.py           # 入口文件
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py   # FastAPI 应用工厂
│       ├── auth.py       # JWT 认证 & 用户管理
│       ├── config.py     # 配置项
│       ├── schemas.py    # 请求模型
│       ├── sql_utils.py  # SQL 工具函数
│       ├── storage/      # 文件存储
│       └── routers/
│           ├── auth_router.py   # 登录/改密
│           ├── admin_router.py  # 用户管理
│           └── data_router.py   # 数据增删查导
├── DEPLOY.md             ← 部署指南
└── README.md
```

## 角色权限

| 角色 | 上传 | 查看 | 删除 | 用户管理 |
|------|------|------|------|---------|
| admin | ✅ | ✅ | ✅ | ✅ |
| editor | ✅ | ✅ | ✅ | ❌ |
| viewer | ❌ | ✅ | ❌ | ❌ |

## 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000

# 前端
cd frontend-vue
npm install
npm run dev
# → http://localhost:5173
```

默认管理员账号：`admin` / `admin123`（首次登录后请立即修改）

## 服务器部署

详见 [DEPLOY.md](./DEPLOY.md)，主要步骤：

1. 本地构建前端 `npm run build`，上传 `dist/` 到服务器
2. 上传后端代码，`docker build` 构建镜像
3. `docker run` 启动容器（端口 9630）
4. Nginx 配置 `/quackbase/` 子路径反向代理

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 签名密钥 | 自动随机生成（每次重启变化）|

> 生产环境请通过环境变量固定 `SECRET_KEY`，否则重启后已登录的 token 会失效。
