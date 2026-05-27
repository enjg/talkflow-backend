"""流式对话引擎"""
import logging
from typing import AsyncGenerator
from .client import mimo_client
from .prompts import build_system_prompt, build_messages

logger = logging.getLogger(__name__)


class ChatEngine:
    """AI 对话引擎
    
    负责编排 Prompt、调用 MiMo API、流式输出。
    自动追踪 token 用量。
    """

    async def stream_chat(
        self,
        history: list[dict],
        user_message: str,
        reply_lang: str = "auto",
        topic: str = "free",
        level: str = "intermediate",
        character_prompt: str | None = None,
        role: str = "user",
        task_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话
        
        Args:
            history: 对话历史
            user_message: 用户消息
            reply_lang: 回复语言
            topic: 对话主题
            level: 难度级别
            character_prompt: 角色提示词
            role: 调用角色（用于 token 追踪，默认 'user'）
            task_id: 关联任务ID
        """
        if character_prompt:
            system_prompt = character_prompt
        else:
            system_prompt = build_system_prompt(reply_lang, topic, level)
        messages = build_messages(history, user_message, system_prompt, reply_lang)

        logger.info(f"开始流式对话: role={role}, reply_lang={reply_lang}, topic={topic}, history_len={len(history)}")

        try:
            generator = await mimo_client.chat_completion(
                messages=messages,
                stream=True,
                temperature=0.8,
                max_tokens=1024,
                presence_penalty=0.6,
                frequency_penalty=0.3,
                role=role,
                task_id=task_id,
            )
            async for chunk in generator:
                yield chunk
        except Exception as e:
            logger.error(f"AI 对话出错: {e}")
            yield f"[抱歉，AI 暂时无法回复，请稍后再试]"


# 全局单例
chat_engine = ChatEngine()
