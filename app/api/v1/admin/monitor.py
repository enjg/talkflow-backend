"""系统监控 API"""
import os
import time
import platform
from fastapi import APIRouter, Depends
from app.api.v1.admin.deps import require_admin

router = APIRouter()


def _get_cpu_info() -> dict:
    """获取 CPU 信息"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        return {
            "percent": cpu_percent,
            "count": cpu_count,
            "freq_current": round(cpu_freq.current, 0) if cpu_freq else None,
            "freq_max": round(cpu_freq.max, 0) if cpu_freq else None,
        }
    except ImportError:
        # 回退: 读取 /proc/loadavg
        try:
            with open("/proc/loadavg", "r") as f:
                parts = f.read().strip().split()
            return {
                "percent": None,
                "load_1m": float(parts[0]),
                "load_5m": float(parts[1]),
                "load_15m": float(parts[2]),
                "count": os.cpu_count(),
            }
        except Exception:
            return {"percent": None, "count": os.cpu_count()}


def _get_memory_info() -> dict:
    """获取内存信息"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
        }
    except ImportError:
        # 回退: 读取 /proc/meminfo
        try:
            info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        info[key] = int(val) * 1024  # kB -> bytes
            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", 0)
            used = total - available
            return {
                "total": total,
                "available": available,
                "used": used,
                "percent": round(used / total * 100, 1) if total > 0 else 0,
                "total_gb": round(total / (1024 ** 3), 2),
                "used_gb": round(used / (1024 ** 3), 2),
            }
        except Exception:
            return {"total": 0, "percent": 0}


def _get_disk_info() -> dict:
    """获取磁盘信息"""
    try:
        import psutil
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
        }
    except Exception:
        import shutil
        total, used, free = shutil.disk_usage("/")
        return {
            "total": total,
            "used": used,
            "free": free,
            "percent": round(used / total * 100, 1) if total > 0 else 0,
            "total_gb": round(total / (1024 ** 3), 2),
            "used_gb": round(used / (1024 ** 3), 2),
            "free_gb": round(free / (1024 ** 3), 2),
        }


@router.get("/system")
async def system_monitor(
    admin=Depends(require_admin),
):
    """系统监控: CPU / 内存 / 磁盘"""
    return {
        "code": 0,
        "data": {
            "cpu": _get_cpu_info(),
            "memory": _get_memory_info(),
            "disk": _get_disk_info(),
            "server": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "uptime_seconds": int(time.time() - psutil.boot_time()) if _has_psutil() else None,
            },
        },
    }


def _has_psutil() -> bool:
    try:
        import psutil  # noqa: F401
        return True
    except ImportError:
        return False
