"""管理端 - 监控中心"""
import shutil
import psutil
from fastapi import APIRouter

router = APIRouter()


@router.get("/monitor/system")
async def system_monitor():
    """系统资源监控"""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    return {
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count(),
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": round(disk.used / disk.total * 100, 1),
        },
    }


@router.get("/monitor/services")
async def service_status():
    """服务状态检查"""
    import socket

    services = [
        {"name": "TalkFlow API", "port": 8000, "desc": "FastAPI后端"},
        {"name": "TalkFlow Frontend", "port": 5173, "desc": "Vue前端开发服务器"},
        {"name": "Dashboard", "port": 8000, "path": "/dashboard", "desc": "工作看板"},
        {"name": "Invitation", "port": 8888, "desc": "邀请函"},
    ]

    results = []
    for svc in services:
        port = svc["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            ok = sock.connect_ex(("127.0.0.1", port)) == 0
            sock.close()
        except Exception:
            ok = False

        results.append({
            "name": svc["name"],
            "port": port,
            "desc": svc["desc"],
            "status": "running" if ok else "stopped",
        })

    return {"services": results}
