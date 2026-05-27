"""语音合成服务 — MiMo TTS（主）+ Edge TTS（备）

MiMo TTS: 小米自研 mimo-v2.5-tts，音质好，支持风格控制
Edge TTS: 微软免费，速度快，作为备用
"""
import os
import re
import io
import logging
import tempfile
import asyncio
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# ====== Edge TTS 音色 =====
EDGE_VOICES = {
    "zh": {
        "白桦": "zh-CN-YunjianNeural",      # 成熟男声，磁性低沉
        "云希": "zh-CN-YunxiNeural",        # 年轻男声，温暖
        "云扬": "zh-CN-YunyangNeural",      # 新闻播报男声
        "晓晓": "zh-CN-XiaoxiaoNeural",    # 年轻女声
        "晓依": "zh-CN-XiaoyiNeural",      # 温柔女声
        "default": "zh-CN-YunjianNeural",
    },
    "en": {
        "白桦": "en-US-GuyNeural",           # 成熟男声
        "Andrew": "en-US-AndrewNeural",      # 温暖男声
        "Emma": "en-US-EmmaNeural",          # 女声
        "default": "en-US-GuyNeural",
    },
}

# 默认风格
DEFAULT_STYLE_ZH = "成熟男性低沉磁性的嗓音，语速平缓从容，像酒吧里的调酒师在和多年老友深夜叙旧，语气温暖放松，偶尔带一点慵懒的笑意，声音浑厚有质感，让人感到安心和舒适"
DEFAULT_STYLE_EN = "Mature male voice, deep and magnetic baritone, slow and relaxed pace, like an old friend catching up over whiskey at a late-night bar, warm and easygoing with a hint of lazy charm, voice is rich and textured"


class TTSService:
    """语音合成服务

    优先使用 MiMo TTS（音质好、支持风格控制）
    MiMo TTS 失败时回退到 Edge TTS
    """

    def __init__(self):
        self._edge_available = True
        self._mimo_available = True
        try:
            import edge_tts
            self._edge_tts = edge_tts
        except ImportError:
            logger.warning("edge-tts 未安装，将使用 MiMo TTS")
            self._edge_available = False

    def _get_edge_voice(self, voice_id: str | None, lang: str) -> str:
        """获取 Edge TTS 音色名"""
        lang_voices = EDGE_VOICES.get(lang, EDGE_VOICES["zh"])
        if voice_id and voice_id in lang_voices:
            return lang_voices[voice_id]
        return lang_voices.get("default", "zh-CN-YunjianNeural")

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        lang: str = "zh",
        style_instruction: str | None = None,
    ) -> tuple[bytes, str] | None:
        """合成语音，返回 (音频bytes, 格式)"""

        # 1. 尝试 Edge TTS（快）
        # 1. 优先 MiMo TTS（音质好、支持风格控制）
        if self._mimo_available:
            try:
                return await self._mimo_synthesize(text, voice_id, lang, style_instruction)
            except Exception as e:
                logger.warning(f"MiMo TTS 失败，回退 Edge: {e}")

        # 2. 回退 Edge TTS
        if self._edge_available:
            try:
                return await self._edge_synthesize(text, voice_id, lang, style_instruction)
            except Exception as e:
                logger.warning(f"Edge TTS 也失败: {e}")

        return None

    async def _edge_synthesize(
        self,
        text: str,
        voice_id: str | None,
        lang: str,
        style_instruction: str | None,
    ) -> bytes | None:
        """Edge TTS 合成"""
        if not text or not text.strip():
            logger.warning("Edge TTS: 文本为空，跳过")
            return None

        voice = self._get_edge_voice(voice_id, lang)
        logger.info(f"Edge TTS 合成: voice={voice}, lang={lang}, text={text[:50]}...")

        communicate = self._edge_tts.Communicate(
            text=text.strip(),
            voice=voice,
            rate="-10%",
            volume="+0%",
        )

        # 收集音频数据（MP3 格式）
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])

        if not audio_data:
            raise Exception("Edge TTS 未返回音频数据")

        logger.info(f"Edge TTS 合成完成: {len(text)} chars → {len(audio_data)} bytes, voice={voice}")
        return bytes(audio_data), "mp3"

    async def _mimo_synthesize(
        self,
        text: str,
        voice_id: str | None,
        lang: str,
        style_instruction: str | None,
    ) -> bytes | None:
        """MiMo TTS 合成（回退方案）"""
        import base64
        import httpx
        from ...config import settings

        voice = voice_id if voice_id and voice_id != "default" else (
            "冰糖" if lang == "zh" else "Mia"
        )

        messages = []
        if style_instruction:
            messages.append({"role": "user", "content": style_instruction})
        else:
            default = DEFAULT_STYLE_ZH if lang == "zh" else DEFAULT_STYLE_EN
            messages.append({"role": "user", "content": default})
        messages.append({"role": "assistant", "content": text})

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.MIMO_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.MIMO_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.MIMO_TTS_MODEL,
                    "messages": messages,
                    "audio": {"format": "wav", "voice": voice},
                },
            )
            resp.raise_for_status()
            data = resp.json()

            audio_data = data.get("choices", [{}])[0].get("message", {}).get("audio", {})
            if not audio_data or not audio_data.get("data"):
                raise Exception("MiMo TTS 响应中无音频数据")

            audio_bytes = base64.b64decode(audio_data["data"])
            logger.info(f"MiMo TTS 合成完成: {len(text)} chars → {len(audio_bytes)} bytes, voice={voice}")
            return audio_bytes, "wav"

    async def synthesize_streaming(
        self,
        text: str,
        voice_id: str | None = None,
        lang: str = "zh",
    ) -> AsyncGenerator[bytes, None]:
        """流式合成（Edge TTS 专属，逐 chunk 返回 MP3）"""
        if not self._edge_available:
            # 回退：整段合成
            audio = await self.synthesize(text, voice_id, lang)
            if audio:
                yield audio
            return

        voice = self._get_edge_voice(voice_id, lang)
        communicate = self._edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="-10%",
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    def get_available_voices(self, lang: str = "zh") -> dict:
        """获取可用音色列表"""
        return {k: v for k, v in EDGE_VOICES.get(lang, EDGE_VOICES["zh"]).items() if k != "default"}


# 全局单例
tts_service = TTSService()
