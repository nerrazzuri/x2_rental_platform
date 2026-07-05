from fastapi import FastAPI

from .platform import router as platform_router

app = FastAPI(title="X2 Rental Local API")
app.include_router(platform_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "x2-local-api",
        "mode": "windows-desktop",
    }


@app.get("/app-mode")
def app_mode():
    return {
        "mode": "admin",
        "available_modes": ["admin", "operator"],
    }
