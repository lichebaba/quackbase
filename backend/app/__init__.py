import logging
import os

# 大文件上传限制（500MB）
MAX_UPLOAD_SIZE = 500 * 1024 * 1024
os.environ["MULTIPART_MAX_MEMORY_SIZE"] = str(MAX_UPLOAD_SIZE)
os.environ["MULTIPART_MAX_FILE_SIZE"] = str(MAX_UPLOAD_SIZE)

# 兼容某些环境下 python-multipart 没有正确读取环境变量的情况：
# 主动覆盖其内部的大小限制（如果对应属性存在）
try:
    import multipart.multipart as _multipart_mod  # type: ignore
    if hasattr(_multipart_mod, "MAX_MEMORY_SIZE"):
        _multipart_mod.MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
    if hasattr(_multipart_mod, "MAX_FILE_SIZE"):
        _multipart_mod.MAX_FILE_SIZE = MAX_UPLOAD_SIZE
except Exception:
    # 如果库内部结构变更，无需影响应用启动
    pass

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from .auth import init_admin
from .routers import auth_router, admin_router, data_router

logger = logging.getLogger("quackbase")
logging.basicConfig(level=logging.INFO)
logger.info(f"Upload size limit: {MAX_UPLOAD_SIZE / 1024 / 1024} MB")


def create_app() -> FastAPI:
    app = FastAPI(title="Quackbase API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 对较大的响应启用 GZip 压缩，显著减少 CSV 导出体积
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # 捕获 multipart 解析错误，返回更有用的提示
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if exc.status_code == 422 and "parsing the body" in str(exc.detail):
            content_length = request.headers.get("content-length", "unknown")
            content_type = request.headers.get("content-type", "unknown")
            logger.error(
                f"Multipart parse error: content-length={content_length}, "
                f"content-type={content_type}, path={request.url.path}"
            )
            return JSONResponse(
                status_code=422,
                content={
                    "detail": f"文件上传解析失败 (content-length: {content_length})。"
                              "可能原因：1) 文件过大，超过 Nginx/服务器限制；"
                              "2) 网络传输中断导致数据不完整。"
                },
            )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.include_router(auth_router.router)
    app.include_router(admin_router.router)
    app.include_router(data_router.router)

    @app.on_event("startup")
    async def startup():
        init_admin()

    @app.get("/")
    async def root():
        return {"status": "ok", "name": "Quackbase", "version": "3.0.0"}

    return app


app = create_app()
