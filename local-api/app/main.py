import os

from fastapi import FastAPI

from .gateway import router as gateway_router
from .platform import router as platform_router


def app_role_from_env() -> str:
    return os.getenv("X2_API_ROLE", "business").strip().lower() or "business"


def create_app(role: str | None = None) -> FastAPI:
    selected_role = (role or app_role_from_env()).strip().lower()
    app = FastAPI(title="X2 Rental Local API")
    if selected_role == "robot-gateway":
        app.include_router(gateway_router)
    else:
        selected_role = "business"
        app.include_router(platform_router)

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "service": "x2-local-api",
            "mode": "windows-desktop" if selected_role == "business" else "x2-pc2-gateway",
            "role": selected_role,
        }

    @app.get("/app-mode")
    def app_mode():
        if selected_role == "robot-gateway":
            return {
                "mode": "robot-gateway",
                "available_modes": ["robot-gateway"],
            }
        return {
            "mode": "admin",
            "available_modes": ["admin", "operator"],
        }

    return app


app = create_app()
