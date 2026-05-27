"""MiMo API 客户端 — OpenAI 兼容接口"""
import json
import asyncio
import logging
from typing import AsyncGenerator
import httpx
from ...config import settings
from .token_tracker import record_usage

logger = logging.getLogger(__name__)


class MiMoClient:
    """MiMo API 异步客户端
    
    使用 httpx 连接池，支持流式输出，自动重试。
    兼容 OpenAI Chat Completion API 格式。
    自动记录每个角色的 token 消耗。
    """

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端（延迟初始化，连接池复用）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.MIMO_BASE_URL,
                headers={
                    "Authorization": f"Bearer {settings.MIMO_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(connect=10, read=120, write=10, pool=10),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        stream: bool = False,
        temperature: float = 0.8,
        max_tokens: int = 2048,
        presence_penalty: float = 0.6,
        frequency_penalty: float = 0.3,
        role: str = "unknown",
        task_id: str | None = None,
    ) -> AsyncGenerator[str, None] | dict:
        """调用聊天补全接口
        
        Args:
            messages: 消息列表
            model: 模型名称，默认使用配置的聊天模型
            stream: 是否流式输出
            temperature: 温度参数
            max_tokens: 最大 token 数
            presence_penalty: 存在惩罚
            frequency_penalty: 频率惩罚
            role: 调用角色标识（用于 token 追踪）
            task_id: 关联任务ID（用于 token 追踪）
            
        Returns:
            流式: AsyncGenerator[str, None] 产出每个 chunk 文本
            非流式: dict 完整响应
        """
        model = model or settings.MIMO_CHAT_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
        }

        if stream:
            # 请求流式 usage 统计（OpenAI 兼容）
            payload["stream_options"] = {"include_usage": True}
            return self._stream_chat(payload, role=role, model=model, task_id=task_id)
        else:
            return await self._normal_chat(payload, role=role, model=model, task_id=task_id)

    async def _normal_chat(self, payload: dict, role: str = "unknown", model: str = "", task_id: str | None = None) -> dict:
        """非流式聊天（带重试）"""
        client = await self._get_client()
        for attempt in range(3):
            try:
                resp = await client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                result = resp.json()
                
                # 记录 token 用量
                usage = result.get("usage", {})
                if usage:
                    record_usage(
                        role=role,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens"),
                        model=payload.get("model", model),
                        task_id=task_id,
                    )
                
                return result
            except (httpx.HTTPStatusError, httpx.ConnectError) as e:
                logger.warning(f"MiMo API 请求失败 (尝试 {attempt+1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    async def _stream_chat(
        self, payload: dict, role: str = "unknown", model: str = "", task_id: str | None = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天（带重试，自动记录 token）"""
        client = await self._get_client()
        for attempt in range(3):
            try:
                collected_content = []
                usage_data = None
                
                async with client.stream(
                    "POST", "/chat/completions", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            
                            # 提取 usage（在最后一个 chunk）
                            if "usage" in chunk and chunk["usage"]:
                                usage_data = chunk["usage"]
                            
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                collected_content.append(content)
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                
                # 流结束后记录 token
                if usage_data:
                    # API 返回了精确的 usage
                    record_usage(
                        role=role,
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens"),
                        model=payload.get("model", model),
                        task_id=task_id,
                    )
                else:
                    # API 未返回 usage，用估算值（中文约 1.5 token/字）
                    output_text = "".join(collected_content)
                    estimated_output = max(1, int(len(output_text) * 1.5))
                    # 输入估算：统计 messages 总长度
                    input_text = json.dumps(payload.get("messages", []), ensure_ascii=False)
                    estimated_input = max(1, int(len(input_text) * 0.4))
                    record_usage(
                        role=role,
                        prompt_tokens=estimated_input,
                        completion_tokens=estimated_output,
                        model=payload.get("model", model),
                        task_id=task_id,
                    )
                    logger.info(f"[TokenTracker] 估算 {role}: ~{estimated_input} in + ~{estimated_output} out")
                
                return  # 正常结束
            except (httpx.HTTPStatusError, httpx.ConnectError) as e:
                logger.warning(f"MiMo 流式请求失败 (尝试 {attempt+1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# 全局单例
mimo_client = MiMoClient()
