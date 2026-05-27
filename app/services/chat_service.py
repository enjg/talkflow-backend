"""对话服务 — 核心业务编排（流式 TTS 版）"""
import json
import re
import logging
import asyncio
import base64 as b64
from uuid import UUID
from typing import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..domain.models.message import Message
from ..domain.models.session import Session
from ..domain.models.user_character import UserCharacter
from ..domain.schemas.chat import SSEChunk
from ..repositories.message_repo import MessageRepository
from ..repositories.session_repo import SessionRepository
from .ai.chat_engine import chat_engine
from .ai.stt_service import stt_service
from .ai.tts_service import tts_service
from .ai.characters import get_character, get_character_prompt, get_character_voice

logger = logging.getLogger(__name__)


def _is_uuid(s: str) -> bool:
    """判断字符串是否是合法 UUID"""
    try:
        UUID(s)
        return True
    except ValueError:
        return False


class ChatService:
    """对话服务 — 编排 AI 对话流程"""

    async def _resolve_session(
        self, db: AsyncSession, session_id: str, user_id: UUID, reply_lang: str | None
    ) -> tuple[Session | None, str | None, str | None]:
        """解析 session_id：如果是 UUID 直接查，如果是角色ID则查找/创建对应 session
        
        返回: (session_obj, character_id, voice_id)
        """
        sess_repo = SessionRepository(db)

        if _is_uuid(session_id):
            # 普通 UUID session
            s = await sess_repo.get_by_id(UUID(session_id))
            return s, None, None

        # 角色ID → 查找该用户下此角色的 session，没有则创建
        character_id = session_id
        char = get_character(character_id)

        # 查找已有 session
        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.character_id == character_id,
                Session.is_active == True,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            voice_id = None
            if char:
                voice_id = char.get("voice_id", {}).get(reply_lang or "zh", "白桦")
            return existing, character_id, voice_id

        # 自定义角色
        if not char and character_id.startswith("custom_"):
            real_id = character_id.replace("custom_", "")
            try:
                result = await db.execute(
                    select(UserCharacter).where(
                        UserCharacter.id == UUID(real_id),
                        UserCharacter.user_id == user_id,
                    )
                )
                uc = result.scalar_one_or_none()
                if uc:
                    char = {"name": uc.name, "voice_id": {"zh": uc.voice_id_zh, "en": uc.voice_id_en}}
            except ValueError:
                pass

        # 创建新 session
        char_name = char["name"] if char else character_id
        new_sess = await sess_repo.create(
            user_id=user_id,
            title=f"与{char_name}的对话",
            topic="character",
            reply_lang=reply_lang or "auto",
        )
        new_sess.character_id = character_id
        await db.commit()

        voice_id = None
        if char and isinstance(char.get("voice_id"), dict):
            voice_id = char["voice_id"].get(reply_lang or "zh", "白桦")
        return new_sess, character_id, voice_id

    async def send_text_message(
        self,
        session: AsyncSession,
        session_id: str,
        user_id: UUID,
        message: str,
        reply_lang: str | None = None,
        enable_voice: bool = False,
        voice_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        msg_repo = MessageRepository(session)

        # 解析 session / 角色
        chat_session, character_id, char_voice = await self._resolve_session(
            session, session_id, user_id, reply_lang
        )
        if not chat_session:
            yield self._sse({"type": "error", "content": "会话不存在"})
            return

        actual_session_id = chat_session.id
        reply_lang = reply_lang or chat_session.reply_lang or "auto"
        topic = chat_session.topic or "free"

        # 使用角色音色（如果未指定）
        if not voice_id and char_voice:
            voice_id = char_voice

        # 1. 保存用户消息
        await msg_repo.create(
            session_id=actual_session_id, role="user", content=message, lang="auto"
        )
        await session.commit()

        # 2. 加载历史上下文
        history_msgs = await msg_repo.get_recent_messages(actual_session_id, limit=20)
        history = [{"role": m.role, "content": m.content} for m in history_msgs]
        if history and history[-1]["role"] == "user":
            history = history[:-1]

        # 3. 获取用户水平
        from ..repositories.user_repo import UserRepository
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        level = user.level if user else "intermediate"

        # 4. 获取角色系统提示词
        char_prompt = None
        if character_id:
            if character_id.startswith("custom_"):
                real_id = character_id.replace("custom_", "")
                try:
                    result = await session.execute(
                        select(UserCharacter).where(
                            UserCharacter.id == UUID(real_id),
                            UserCharacter.user_id == user_id,
                        )
                    )
                    uc = result.scalar_one_or_none()
                    if uc and uc.system_prompt:
                        char_prompt = uc.system_prompt
                except ValueError:
                    pass
            else:
                char_prompt = get_character_prompt(character_id, reply_lang)

        # 5. 生成开始
        import uuid
        ai_msg_id = str(uuid.uuid4())
        yield self._sse({"type": "start", "message_id": ai_msg_id})

        # 6. 流式 AI 回复 + 实时 TTS
        full_text = ""
        sentence_buf = ""
        tts_audio_idx = 0
        tts_tasks = []

        _tts_lang_map = {"zh": "zh", "en": "en"}
        tts_lang = _tts_lang_map.get(reply_lang, None)

        async def _tts_chunk(idx: int, text: str, lang: str):
            result = await tts_service.synthesize(text, voice_id=voice_id, lang=lang)
            if result:
                audio, fmt = result
                return idx, audio, fmt
            return idx, None, "mp3"

        def _flush_sentences(text_so_far: str):
            parts = re.split(r'(?<=[。！？.!?\n])', text_so_far)
            if len(parts) <= 1:
                return [], text_so_far
            complete = [p.strip() for p in parts[:-1] if p.strip()]
            remainder = parts[-1]
            return complete, remainder

        def _merge_short(sentences: list[str], max_chars: int = 80) -> list[str]:
            chunks = []
            current = ""
            for s in sentences:
                if len(current) + len(s) <= max_chars:
                    current += s
                else:
                    if current:
                        chunks.append(current)
                    if len(s) > max_chars:
                        sub = re.split(r'(?<=[，,;；])', s)
                        buf = ""
                        for p in sub:
                            if len(buf) + len(p) <= max_chars:
                                buf += p
                            else:
                                if buf:
                                    chunks.append(buf)
                                buf = p
                        current = buf
                    else:
                        current = s
            if current:
                chunks.append(current)
            return chunks if chunks else sentences

        try:
            async for chunk in chat_engine.stream_chat(
                history=history,
                user_message=message,
                reply_lang=reply_lang,
                topic=topic,
                level=level,
                character_prompt=char_prompt,
            ):
                full_text += chunk
                sentence_buf += chunk
                yield self._sse({"type": "chunk", "content": chunk})

                if not tts_lang and len(full_text) < 20:
                    tts_lang = self._detect_lang(full_text)

                if enable_voice:
                    sentences, sentence_buf = _flush_sentences(sentence_buf)
                    if sentences:
                        merged = _merge_short(sentences)
                        for m in merged:
                            t = asyncio.create_task(
                                _tts_chunk(tts_audio_idx, m, tts_lang or "zh")
                            )
                            tts_tasks.append(t)
                            tts_audio_idx += 1

                        done = [t for t in tts_tasks if t.done()]
                        for t in done:
                            tts_tasks.remove(t)
                            try:
                                idx, audio_bytes, fmt = t.result()
                                if audio_bytes:
                                    audio_b64 = b64.b64encode(audio_bytes).decode("utf-8")
                                    yield self._sse({
                                        "type": "audio",
                                        "audio_data": audio_b64,
                                        "format": fmt,
                                        "index": idx,
                                    })
                            except Exception as e:
                                logger.warning(f"流式 TTS 段失败: {e}")

        except Exception as e:
            logger.error(f"AI 流式对话出错: {e}")
            yield self._sse({"type": "error", "content": "AI 回复中断"})

        if not tts_lang:
            tts_lang = self._detect_lang(full_text)

        if enable_voice and sentence_buf.strip():
            remaining = sentence_buf.strip()
            merged = _merge_short([remaining])
            for m in merged:
                t = asyncio.create_task(
                    _tts_chunk(tts_audio_idx, m, tts_lang)
                )
                tts_tasks.append(t)
                tts_audio_idx += 1

        if tts_tasks:
            results = await asyncio.gather(*tts_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"TTS 段失败: {result}")
                    continue
                idx, audio_bytes, fmt = result
                if audio_bytes:
                    audio_b64 = b64.b64encode(audio_bytes).decode("utf-8")
                    yield self._sse({
                        "type": "audio",
                        "audio_data": audio_b64,
                        "format": fmt,
                        "index": idx,
                    })

        ai_msg = await msg_repo.create(
            session_id=actual_session_id,
            role="assistant",
            content=full_text,
            lang=tts_lang or "unknown",
        )
        await session.commit()

        yield self._sse({
            "type": "done",
            "message_id": str(ai_msg.id),
            "full_text": full_text,
            "lang": tts_lang or "unknown",
        })

        await sess_repo.update(actual_session_id)
        await session.commit()

    async def send_audio_message(
        self,
        session: AsyncSession,
        session_id: str,
        user_id: UUID,
        audio_bytes: bytes,
        audio_format: str = "webm",
        reply_lang: str | None = None,
    ) -> AsyncGenerator[str, None]:
        result = await stt_service.transcribe(audio_bytes, audio_format)
        text = result["text"]
        detected_lang = result["lang"]

        if not text:
            yield self._sse({"type": "error", "content": "语音识别失败，请重试"})
            return

        yield self._sse({"type": "transcript", "text": text, "lang": detected_lang})

        async for chunk in self.send_text_message(
            session, session_id, user_id, text, reply_lang
        ):
            yield chunk

    def _sse(self, data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _detect_lang(self, text: str) -> str:
        if not text:
            return "unknown"
        cn = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        ratio = cn / len(text)
        if ratio > 0.5:
            return "zh"
        elif ratio < 0.1:
            return "en"
        return "mixed"


chat_service = ChatService()