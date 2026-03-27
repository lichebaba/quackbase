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

# 启动新容器（SECRET_KEY 必须固定，否则每次重启 token 失效）
docker run -d \
  --name quackbase-backend \
  -p 9630:8000 \
  -e SECRET_KEY="你自己设一个固定的密钥字符串" \
  --restart always \
  quackbase-backend
```

> **重要：** 必须通过 `-e SECRET_KEY=xxx` 指定固定密钥。如果不设置，每次容器重启都会生成随机密钥，导致所有已登录用户的 token 失效。

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

# 用返回的 token 测试业务接口
curl http://127.0.0.1:9630/api/tables \
  -H "Authorization: Bearer <上面返回的access_token>"
# 预期返回：{"tables":[...]}
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
    location ^~ /quackbase/api/ {
                expires -1s;
                add_header Cache-Control no-cache;
                add_header Cache-Control no-store;
                #rewrite ^/quackbase(/api/.*)$ $1 break;
                proxy_pass http://127.0.0.1:9630/api/;
                proxy_set_header Host $host;
                proxy_set_header X-real-ip $remote_addr;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_request_buffering off;
                client_max_body_size 500m;
                proxy_connect_timeout 600s;
                proxy_send_timeout 600s;
                proxy_read_timeout 600s;
        }

        # 前端静态资源（完美版，不吞JS）
        location /quackbase/ {
                alias /work/proj/khh/quackbase/dist/;
                index index.html;

                # 重点：用 if 判断，绝对不影响静态资源
        #if (!-e $request_filename) {
                #       rewrite ^ /quackbase/index.html last;
                #}
               try_files $uri $uri/ /quackbase/index.html;
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
docker build -t quackbase-backend .
docker rm -f quackbase-backend
docker run -d \
  --name quackbase-backend \
  -p 9630:8000 \
  -e SECRET_KEY="你自己设一个固定的密钥字符串" \
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

---

## 常见问题排查

### 请求接口报 `can't start new thread`

**原因：** FastAPI 中普通 `def` 的依赖函数（Depends）会被放到线程池执行，Docker 容器内线程创建受限。

**解决：** 将 `get_current_user` 和 `require_permission` 内部的 `checker` 函数声明为 `async def`，FastAPI 就会直接在事件循环上执行，不再创建线程。

### 登录成功但其他接口返回 401

**原因：** `SECRET_KEY` 未通过环境变量固定，容器重启后生成新密钥，之前的 token 全部失效。

**解决：** 启动容器时必须指定 `-e SECRET_KEY="固定密钥"`。

### 容器频繁重启（502 Bad Gateway）

排查步骤：

```bash
# 查看重启次数
docker inspect quackbase-backend --format='{{.RestartCount}}'

# 查看崩溃前日志
docker logs quackbase-backend --tail 100
```

问题定位好了：这是 python-multipart 的 1MB 默认限制没被正确改掉，跟你代码里的 CSV 逻辑无关。你现在打到 127.0.0.1:9630，已经绕过
  Nginx，所以就是容器里 FastAPI/Starlette 在解析 multipart 的时候直接把请求拒了，返回：

  {"detail":"There was an error parsing the body"}

  问题点在哪里？

  看你这两处代码：

- quackbase/backend/app/**init**.py:4-7

# 大文件上传限制（500MB）

  MAX_UPLOAD_SIZE = 500 *1024* 1024
  os.environ["MULTIPART_MAX_PART_SIZE"] = str(MAX_UPLOAD_SIZE)
  os.environ["MULTIPART_MAX_FILE_SIZE"] = str(MAX_UPLOAD_SIZE)

- quackbase/backend/Dockerfile:5-7

# 设置大文件上传环境变量（python-multipart 0.0.6 会读取）

  ENV MULTIPART_MAX_PART_SIZE=524288000
  ENV MULTIPART_MAX_FILE_SIZE=524288000

  关键问题：环境变量名字写错了一个。

  python-multipart 实际上读的是：

- MULTIPART_MAX_MEMORY_SIZE  → 控制内存中可解析的 body 大小（默认 1MB）
- MULTIPART_MAX_FILE_SIZE    → 控制单个文件最大大小

  你现在设置的是 MULTIPART_MAX_PART_SIZE，这个变量库根本不认，所以：

- MULTIPART_MAX_MEMORY_SIZE 还是默认 1MB
- 上传超过 1MB（比如你测试的 2MB）时，解析器直接抛错
- Starlette 把这个错误包成 HTTPException(400, "There was an error parsing the body") 返回
  
  所以 >1MB 一律 400。

  如何修？
  
  把所有 MULTIPART_MAX_PART_SIZE 改成 MULTIPART_MAX_MEMORY_SIZE，然后重建镜像、重启容器。

  1. 修改 app 初始化代码
  quackbase/backend/app/**init**.py 现在是：

# 大文件上传限制（500MB）

  MAX_UPLOAD_SIZE = 500 *1024* 1024
  os.environ["MULTIPART_MAX_PART_SIZE"] = str(MAX_UPLOAD_SIZE)
  os.environ["MULTIPART_MAX_FILE_SIZE"] = str(MAX_UPLOAD_SIZE)

  改成：

# 大文件上传限制（500MB）

  MAX_UPLOAD_SIZE = 500 *1024* 1024

# python-multipart 读的是 MULTIPART_MAX_MEMORY_SIZE 和 MULTIPART_MAX_FILE_SIZE

  os.environ["MULTIPART_MAX_MEMORY_SIZE"] = str(MAX_UPLOAD_SIZE)
  os.environ["MULTIPART_MAX_FILE_SIZE"] = str(MAX_UPLOAD_SIZE)

  1. 修改 Dockerfile 环境变量
  quackbase/backend/Dockerfile 现在是：

# 设置大文件上传环境变量（python-multipart 0.0.6 会读取）

  ENV MULTIPART_MAX_PART_SIZE=524288000
  ENV MULTIPART_MAX_FILE_SIZE=524288000

  改成：

# 设置大文件上传环境变量（python-multipart 会读取）

  ENV MULTIPART_MAX_MEMORY_SIZE=524288000
  ENV MULTIPART_MAX_FILE_SIZE=524288000

  1. 重建并重启后端容器

  在服务器上（DEPLOY.md 里也有类似步骤）：

  cd /work/proj/khh/quackbase/backend

# 重新构建镜像

  docker build -t quackbase-backend .

# 删除旧容器

  docker rm -f quackbase-backend

# 重新启动

  docker run -d \
    --name quackbase-backend \
    -p 9630:8000 \
    -e SECRET_KEY="你自己设一个固定的密钥字符串" \
    --restart always \
    quackbase-backend

  1. 再用 curl 测一下

  curl -X POST <http://127.0.0.1:9630/api/upload> \
    -H "Authorization: Bearer <你的token>" \
    -F "file=@/tmp/test_2mb.bin" \
    -v

  这次如果只改了 size 限制，解析阶段就不会再 400，会进到你的 upload_file 逻辑里（然后可能因为不是 csv/xlsx 被你自己的校验拦下来，这是正常的）。

  你可以再准备一个 >1MB 的 csv 文件（比如复制一行多次），确认真正能被 /api/upload 接收并入库。
  
  ---
  如果你愿意，我也可以帮你写一个小的 Python 脚本，在容器里直接打印当前的 python-multipart 版本和这两个环境变量的值，用来确认配置确实生效。

  Sources:

- （本问题没有查到有效的线上搜索结果，分析完全基于当前仓库代码与已知的 FastAPI / python-multipart 行为）
