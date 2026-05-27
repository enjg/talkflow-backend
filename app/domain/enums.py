"""
枚举模块 - 定义应用中使用的各种枚举类型。
"""
from enum import Enum


class Language(str, Enum):
    """支持的语言。"""
    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"
    HINDI = "hi"


class Role(str, Enum):
    """对话角色。"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Emotion(str, Enum):
    """AI 情感标签。"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ENCOURAGING = "encouraging"
    THOUGHTFUL = "thoughtful"
    SURPRISED = "surprised"
    CURIOUS = "curious"


class Topic(str, Enum):
    """对话主题。"""
    DAILY = "daily"
    INTERVIEW = "interview"
    TRAVEL = "travel"
    BUSINESS = "business"
    ACADEMIC = "academic"
    CASUAL = "casual"
    CUSTOM = "custom"


class Level(str, Enum):
    """语言水平。"""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    NATIVE = "native"
