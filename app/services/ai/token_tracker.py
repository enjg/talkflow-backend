"""Token 用量追踪器 — 按角色记录每次 MiMo API 调用的 token 消耗"""
import json
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 统计文件路径
STATS_DIR = Path(os.getenv("TOKEN_STATS_DIR", "/home/ubuntu/dashboard"))
STATS_FILE = STATS_DIR / "token_stats.json"
CST = timezone(timedelta(hours=8))


def _load_stats() -> dict:
    """加载统计数据"""
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {"daily": {}, "total": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}}


def _save_stats(data: dict):
    """保存统计数据（原子写入）"""
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.rename(STATS_FILE)


def record_usage(
    role: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int | None = None,
    model: str = "",
    task_id: str | None = None,
):
    """记录一次 API 调用的 token 用量
    
    Args:
        role: 角色标识，如 'qm-fe', 'qm-be', 'user' 等
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        total_tokens: 总 token 数（可选，自动计算）
        model: 使用的模型名
        task_id: 关联的任务ID
    """
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens

    now = datetime.now(CST)
    today = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H")

    data = _load_stats()

    # 初始化今日数据
    if today not in data["daily"]:
        data["daily"][today] = {}
    if role not in data["daily"][today]:
        data["daily"][today][role] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "calls": 0,
            "tasks": [],
            "hourly": {},
        }

    role_stats = data["daily"][today][role]

    # 累加统计
    role_stats["prompt_tokens"] += prompt_tokens
    role_stats["completion_tokens"] += completion_tokens
    role_stats["total_tokens"] += total_tokens
    role_stats["calls"] += 1

    # 按小时统计
    if hour not in role_stats["hourly"]:
        role_stats["hourly"][hour] = {"tokens": 0, "calls": 0}
    role_stats["hourly"][hour]["tokens"] += total_tokens
    role_stats["hourly"][hour]["calls"] += 1

    # 记录任务关联
    if task_id:
        role_stats["tasks"].append({
            "task_id": task_id,
            "tokens": total_tokens,
            "time": now.strftime("%H:%M:%S"),
        })

    # 更新总计
    data["total"]["prompt_tokens"] += prompt_tokens
    data["total"]["completion_tokens"] += completion_tokens
    data["total"]["total_tokens"] += total_tokens
    data["total"]["calls"] += 1

    _save_stats(data)
    logger.debug(f"[TokenTracker] {role} +{total_tokens} tokens ({prompt_tokens} in + {completion_tokens} out)")


def get_today_stats() -> dict:
    """获取今日各角色统计"""
    data = _load_stats()
    today = datetime.now(CST).strftime("%Y-%m-%d")
    return data.get("daily", {}).get(today, {})


def get_all_stats() -> dict:
    """获取完整统计数据"""
    return _load_stats()


def get_today_summary() -> list[dict]:
    """获取今日汇总（适配看板展示）"""
    today_stats = get_today_stats()
    summary = []
    for role, stats in sorted(today_stats.items()):
        summary.append({
            "role": role,
            "prompt_tokens": stats["prompt_tokens"],
            "completion_tokens": stats["completion_tokens"],
            "total_tokens": stats["total_tokens"],
            "calls": stats["calls"],
            "tasks_count": len(stats.get("tasks", [])),
            "last_active": stats.get("tasks", [{}])[-1].get("time", "") if stats.get("tasks") else "",
        })
    return summary
