# ⚙️ TalkFlow 后端

AI口语对话练习平台 - API服务 (FastAPI)

## 技术栈
- Python 3.11 + FastAPI
- SQLAlchemy (async) + Pydantic v2
- MiMo v2.5-pro (AI对话) + MiMo TTS (语音)
- JWT认证

## 开发
```bash
pip install -r requirements.txt
cp .env.example .env  # 配置API密钥
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API文档
启动后访问: http://localhost:8000/docs

## 项目结构
```
app/
├── api/v1/       # API路由
├── core/         # 核心模块 (安全/异常)
├── domain/       # 领域层
│   ├── models/   # SQLAlchemy模型
│   └── schemas/  # Pydantic模式
├── middleware/   # 中间件
├── repositories/ # 数据访问层
└── services/     # 业务逻辑
    └── ai/       # AI服务 (对话/TTS/STT)
```

## 环境变量
```env
MIMO_API_KEY=your_key
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
JWT_SECRET=your_secret
DATABASE_URL=sqlite+aiosqlite:///./data/ai_spoken.db
```
