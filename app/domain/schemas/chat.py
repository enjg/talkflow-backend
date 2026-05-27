"""对话相关 Schema"""
from uuid import UUID
from pydantic import BaseModel, Field


class ChatSendRequest(BaseModel):
    """发送文字消息请求"""
    session_id: str
    message: str = Field(..., min_length=1, max_length=5000)
    reply_lang: str | None = None
    enable_voice: bool = False
    voice_id: str | None = None


class ChatAudioRequest(BaseModel):
    """发送语音消息请求（用于 WebSocket）"""
    session_id: str
    audio_base64: str
    reply_lang: str | None = None


class InterruptRequest(BaseModel):
    """中断 AI 生成请求"""
    session_id: str
    message_id: str


class SSEChunk(BaseModel):
    """SSE 流式响应块"""
    type: str  # start, chunk, emotion, transcript, done, error
    content: str | None = None
    emotion: str | None = None
    message_id: str | None = None
    lang: str | None = None
    full_text: str | None = None
    audio_url: str | None = None


class MessageResponse(BaseModel):
    """单条消息响应"""
    id: UUID
    role: str
    content: str
    lang: str | None = None
    emotion: str | None = None
    audio_url: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
