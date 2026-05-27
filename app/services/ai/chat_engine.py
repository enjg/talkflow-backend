"""流式对话引擎"""
import logging
from typing import AsyncGenerator
from .client import mimo_client
from .prompts import build_system_prompt, build_messages

logger = logging.getLogger(__name__)


class ChatEngine:
    """AI 对话引擎
    
    负责编排 Prompt、调用 MiMo API、流式输出。
    """

    async def stream_chat(
        self,
        history: list[dict],
        user_message: str,
        reply_lang: str = "auto",
        topic: str = "free",
        level: str = "intermediate",
        character_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        if character_prompt:
            system_prompt = character_prompt
        else:
            system_prompt = build_system_prompt(reply_lang, topic, level)
        messages = build_messages(history, user_message, system_prompt, reply_lang)

        logger.info(f"开始流式对话: reply_lang={reply_lang}, topic={topic}, history_len={len(history)}")

        try:
            generator = await mimo_client.chat_completion(
                messages=messages,
                stream=True,
                temperature=0.8,
                max_tokens=1024,
                presence_penalty=0.6,
                frequency_penalty=0.3,
            )
            async for chunk in generator:
                yield chunk
        except Exception as e:
            logger.error(f"AI 对话出错: {e}")
            yield f"[抱歉，AI 暂时无法回复，请稍后再试]"


# 全局单例
chat_engine = ChatEngine()
