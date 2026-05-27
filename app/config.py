"""应用配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "ai-spoken-practice"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库 (默认 SQLite，生产环境用 PostgreSQL)
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/ai_spoken.db"

    # Redis (可选)
    REDIS_URL: str = ""

    # MiMo AI
    MIMO_API_KEY: str = ""
    MIMO_BASE_URL: str = "https://token-plan-cn.xiaomimimo.com/v1"
    MIMO_CHAT_MODEL: str = "mimo-v2.5-pro"
    MIMO_OMNI_MODEL: str = "mimo-v2-omni"
    MIMO_TTS_MODEL: str = "mimo-v2.5-tts"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]

    # 频率限制
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
