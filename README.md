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

## 后端知识点

  1. FastAPI 的 async def vs def

- async def 路由/依赖 → 直接在事件循环线程上执行，不创建线程
- def 路由/依赖 → FastAPI 自动用 run_in_threadpool 在线程池中执行，每次需要线程
- 这是本次 bug 的根因：Depends() 里的 def 函数在 Docker 受限环境下创建线程失败

  1. DuckDB 连接管理

- duckdb.connect() 每次创建新连接，内部会创建线程（默认=CPU核心数）
- config={"threads": "1"} 限制查询执行线程数
- 连接复用（缓存）比每次新建+close 更高效，避免线程频繁创建销毁

  1. JWT SECRET_KEY 管理

- 密钥随机生成的话，进程重启后所有 token 失效
- 生产环境必须通过环境变量注入固定密钥

  1. Docker 部署

- docker logs 查日志，docker inspect --format='{{.RestartCount}}' 查重启次数
- --restart always 会自动重启崩溃的容器，但可能掩盖问题
- -e 注入环境变量是容器化应用配置的标准做法

  1. 错误排查方法论

- 先看完整 traceback，精确定位出错的代码行
- 不要猜，堆栈会告诉你答案（本次堆栈明确指向 solve_dependencies → run_in_threadpool）

  ## 前端知识点（打包相关）

  1. Vite 多环境配置

- .env.development / .env.production 自动按 mode 加载
- npm run dev → development，npm run build → production
- VITE_ 前缀的变量才会暴露给前端代码

  1. vite.config.js 中的 base 路径

- base: env.VITE_BASE_PATH 控制打包后所有资源的基础路径
- 子路径部署（如 /quackbase/）必须设置 base，否则 JS/CSS 路径会 404

  1. 开发代理 vs 生产反向代理

- 开发时 vite.config.js 的 server.proxy 解决跨域（前端 5173 → 后端 8000）
- 生产时由 Nginx proxy_pass + rewrite 完成同样的事情
