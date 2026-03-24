# QuackBase 部署指南

> 前端部署在宿主机 Nginx 上（子路径 `/quackbase/`），后端使用 Docker 镜像部署。

---

## 环境要求

| 项目       | 要求                                          |
| ---------- | --------------------------------------------- |
| 服务器系统 | CentOS 7 / Ubuntu / Debian 等 Linux           |
| Nginx      | 宿主机已安装，已有其他项目占用 80 端口        |
| Docker     | 已安装                                        |
| Node.js    | 本地有即可（用于构建前端，服务器上不需要）    |

---

## 整体架构

```text
浏览器访问 http://服务器IP/quackbase/
        │
        ▼
┌─── 宿主机 Nginx (:80) ───────────────────────────┐
│                                                    │
│  /quackbase/       → 静态文件 (Vue dist)           │
│  /quackbase/api/   → 反向代理到 127.0.0.1:9630     │
│                                                    │
│  /其他项目/        → 其他项目（互不影响）            │
└────────────────────────────────────────────────────┘
        │
        ▼ proxy_pass
┌─── Docker 容器 (quackbase-backend) ────────────────┐
│                                                     │
│  端口映射:  宿主机 9630 → 容器 8000                  │
│  uvicorn app:app --loop asyncio --http h11          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

服务器上的目录结构：

```text
/work/proj/khh/quackbase/
├── backend/          ← 后端 Python 代码
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
└── dist/             ← 前端构建产物
```

---

## 第一步：前端构建（在本地开发机上操作）

### 1.1 环境配置（已内置，无需手动修改代码）

项目通过 `.env` 文件区分开发/生产环境，Vite 会自动加载：

| 文件               | 生效时机        | VITE_BASE_PATH  | 说明              |
| ------------------ | --------------- | --------------- | ----------------- |
| `.env.development` | `npm run dev`   | `/`             | 本地开发，根路径  |
| `.env.production`  | `npm run build` | `/quackbase/`   | 生产部署，子路径  |

> 如需修改生产子路径，只改 `.env.production` 中的 `VITE_BASE_PATH` 即可，不用动任何代码。

### 1.2 安装依赖并构建

```bash
cd quackbase/frontend-vue
npm install
npm run build
```

构建完成后会生成 `dist/` 目录。

### 1.3 上传到服务器

```bash
# 首次部署需要先创建目录
ssh root@服务器IP "mkdir -p /work/proj/khh/quackbase"

# 上传前端构建产物
scp -r dist/ root@服务器IP:/work/proj/khh/quackbase/dist
```

---

## 第二步：后端部署（在服务器上操作）

### 2.1 上传后端代码到服务器

在**本地终端**执行：

```bash
scp -r quackbase/backend/ root@服务器IP:/work/proj/khh/quackbase/backend/
```

### 2.2 构建 Docker 镜像

SSH 登录服务器后执行：

```bash
cd /work/proj/khh/quackbase/backend
docker build -t quackbase-backend .
```

### 2.3 启动后端容器

```bash
# 如果之前有旧容器，先删除
docker rm -f quackbase-backend 2>/dev/null

# 启动新容器
 docker run -d --name quackbase-backend -p 9630:8000  quackbase-backend
```

curl <http://127.0.0.1:9630/api/tables> \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4NDUwY2NmZi01NzZlLTQzYTgtOTQ0ZC03NTE3ODM5MWFiMGUiLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzc0NDExMTQyfQ.FvqCbUXXvOTQYptAzvlBZoXauovZBzWTYRvUKM9v0Lw"

### 2.4 验证后端是否启动成功

```bash
# 测试根路径
curl http://127.0.0.1:9630/
# 预期返回：{"status":"ok","name":"Quackbase","version":"3.0.0"}

# 测试登录接口
curl -X POST http://127.0.0.1:9630/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# 预期返回：{"access_token":"...","token_type":"bearer","user":{...}}
```

如果报错，查看日志：

```bash
docker logs quackbase-backend --tail 20
```

---

## 第三步：配置 Nginx（在服务器上操作）

在已有的 Nginx 配置中（如 `khh.conf`），找到需要挂载的 `server` 块，加入以下内容：

```nginx
# ===== QuackBase 数据管理平台 =====
# 前端静态文件
location /quackbase {
    alias /work/proj/khh/quackbase/dist;
    index index.html index.htm;
    try_files $uri $uri/ /quackbase/index.html;
}

# 后端 API 反向代理
location /quackbase/api/ {
    expires -1s;
    add_header Cache-Control no-cache;
    add_header Cache-Control no-store;
    rewrite ^/quackbase(/api/.*)$ $1 break;
    proxy_pass http://127.0.0.1:9630;
    proxy_set_header Host $host;
    proxy_set_header X-real-ip $remote_addr;
    proxy_set_header X-Forwarded-For $remote_addr;
    client_max_body_size 500m;
}
```

测试配置并重载：

```bash
nginx -t && nginx -s reload
```

---

## 第四步：访问验证

浏览器打开：

```text
http://服务器IP/quackbase/
```

默认管理员账号：

| 项目   | 值        |
| ------ | --------- |
| 用户名 | admin     |
| 密码   | admin123  |

> 登录后请立即修改密码！

---

## 日常运维

### 更新前端代码

在本地执行：

```bash
# 1. 构建
cd frontend-vue && npm run build

# 2. 上传覆盖
scp -r dist/ root@服务器IP:/work/proj/khh/quackbase/dist

# 不需要重启任何服务，静态文件直接生效
```

### 更新后端代码

```bash
# 1. 本地上传代码
scp -r backend/ root@服务器IP:/work/proj/khh/quackbase/backend/

# 2. 服务器上重新构建镜像并重启
cd /work/proj/khh/quackbase/backend


docker rm -f quackbase-backend
docker run -d \
  --name quackbase-backend \
  -p 9630:8000 \
  --restart always \
  quackbase-backend
```

### 查看后端日志

```bash
docker logs quackbase-backend              # 查看全部日志
docker logs quackbase-backend --tail 50 -f # 实时跟踪最近 50 行
```

### 停止 / 删除后端

```bash
docker stop quackbase-backend    # 停止
docker rm quackbase-backend      # 删除容器
```

---

## 端口总结

| 组件        | 端口 | 说明                                       |
| ----------- | ---- | ------------------------------------------ |
| Nginx       | 80   | 宿主机对外，和其他项目共用                 |
| Docker 后端 | 9630 | 映射到容器内 8000，仅 127.0.0.1 本地可访问 |

> 阿里云安全组只需放行 80 端口，9630 不需要对外开放。
