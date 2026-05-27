"""FastAPI 应用入口"""
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.dependencies import engine
from app.domain.models.base import Base
from app.domain.models.user import User
from app.domain.models.session import Session
from app.domain.models.message import Message
from app.domain.models.user_stats import UserStats
from app.domain.models.user_character import UserCharacter
from app.api.v1.router import api_router
from app.middleware.request_logging import RequestLoggingMiddleware

DASHBOARD_DIR = "/home/ubuntu/ai-spoken-practice/dashboard"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    os.makedirs("data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库已初始化")
    yield
    await engine.dispose()


app = FastAPI(title="TalkFlow", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"name": "TalkFlow", "version": "1.0.0"}


# ========== 工作看板 ==========
@app.get("/dashboard")
async def dashboard_page():
    return FileResponse(os.path.join(DASHBOARD_DIR, "work-report.html"))


@app.get("/api/work-report")
async def get_work_report():
    data_file = os.path.join(DASHBOARD_DIR, "work-data.json")
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return JSONResponse(json.load(f))
    return JSONResponse({})


@app.post("/api/work-report")
async def update_work_report(request: Request):
    data_file = os.path.join(DASHBOARD_DIR, "work-data.json")
    body = await request.json()
    current = {}
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            current = json.load(f)
    current.update(body)
    with open(data_file, "w") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    return {"ok": True}
