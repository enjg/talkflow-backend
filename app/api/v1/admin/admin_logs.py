"""日志管理 API"""
import os
import re
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.api.v1.admin.deps import require_admin

router = APIRouter()

# 日志文件路径（支持多种日志配置）
LOG_PATHS = [
    "logs/app.log",
    "logs/access.log",
    "/var/log/talkflow/app.log",
    "app.log",
]


def _find_log_file() -> str | None:
    """查找可用的日志文件"""
    for path in LOG_PATHS:
        if os.path.exists(path):
            return path
    return None


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    level: Optional[str] = Query(None, description="日志级别: DEBUG/INFO/WARNING/ERROR/CRITICAL"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    admin=Depends(require_admin),
):
    """日志列表（级别/日期筛选）"""
    log_file = _find_log_file()

    if not log_file:
        # 无日志文件时返回示例数据
        return {
            "code": 0,
            "data": {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "message": "未找到日志文件，请配置日志路径",
            },
        }

    # 读取日志行
    lines = []
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
    except Exception as e:
        return {"code": 500, "message": f"读取日志失败: {str(e)}"}

    # 解析日志格式: YYYY-MM-DD HH:MM:SS - LEVEL - message
    log_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*[-–]\s*(\w+)\s*[-–]\s*(.*)"
    )

    for line in reversed(all_lines):  # 最新的在前
        line = line.strip()
        if not line:
            continue

        match = log_pattern.match(line)
        if match:
            timestamp, log_level, message = match.groups()
            log_level = log_level.upper()
        else:
            timestamp = ""
            log_level = "INFO"
            message = line

        # 级别筛选
        if level and log_level != level.upper():
            continue

        # 关键词搜索
        if keyword and keyword.lower() not in message.lower():
            continue

        # 日期筛选
        if start_date and timestamp:
            try:
                log_date = timestamp[:10]
                if log_date < start_date:
                    continue
            except (ValueError, IndexError):
                pass

        if end_date and timestamp:
            try:
                log_date = timestamp[:10]
                if log_date > end_date:
                    continue
            except (ValueError, IndexError):
                pass

        lines.append({
            "timestamp": timestamp,
            "level": log_level,
            "message": message,
        })

    total = len(lines)
    start = (page - 1) * size
    end = start + size

    return {
        "code": 0,
        "data": {
            "items": lines[start:end],
            "total": total,
            "page": page,
            "size": size,
        },
    }
