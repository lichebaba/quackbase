from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import init_admin
from .routers import auth_router, admin_router, data_router


def create_app() -> FastAPI:
    app = FastAPI(title="Quackbase API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
