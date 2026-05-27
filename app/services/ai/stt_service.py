"""语音识别服务 — 使用 MiMo Omni 模型"""
import base64
import logging
from ...config import settings

logger = logging.getLogger(__name__)


class STTService:
    """语音转文字服务
    
    使用 mimo-v2-omni 多模态模型识别语音内容。
    """

    async def transcribe(self, audio_bytes: bytes, audio_format: str = "webm") -> dict:
        """将音频转为文字
        
        Args:
            audio_bytes: 音频二进制数据
            audio_format: 音频格式 (webm/wav/mp3)
            
        Returns:
            {"text": "识别的文字", "lang": "检测到的语言"}
        """
        import httpx

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # 使用 omni 模型的多模态能力识别音频
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "audio": {
                            "data": audio_b64,
                            "format": audio_format,
                        },
                    },
                    {
                        "type": "text",
                        "text": "请识别这段音频中的语音内容，只输出识别到的文字，不要添加任何其他内容。如果混合了多种语言，保持原样输出。",
                    },
                ],
            }
        ]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{settings.MIMO_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.MIMO_API_KEY}"},
                    json={
                        "model": settings.MIMO_OMNI_MODEL,
                        "messages": messages,
                        "max_tokens": 1024,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            text = data["choices"][0]["message"]["content"].strip()
            # 简单语言检测
            lang = self._detect_lang(text)
            logger.info(f"语音识别完成: lang={lang}, len={len(text)}")
            return {"text": text, "lang": lang}

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return {"text": "", "lang": "unknown"}

    def _detect_lang(self, text: str) -> str:
        """简单语言检测：根据字符比例判断"""
        if not text:
            return "unknown"
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        ratio = chinese_chars / len(text)
        if ratio > 0.5:
            return "zh"
        elif ratio < 0.1:
            return "en"
        else:
            return "mixed"


# 全局单例
stt_service = STTService()
