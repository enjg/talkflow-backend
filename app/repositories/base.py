"""通用数据仓库基类"""
import uuid
from typing import TypeVar, Generic, Sequence
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..domain.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """通用异步 CRUD 仓库基类
    
    提供基础的数据库操作，子类可扩展特定查询。
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        """根据 ID 获取记录"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, page: int = 1, size: int = 20, **filters
    ) -> tuple[Sequence[ModelType], int]:
        """分页获取记录列表，返回 (items, total)"""
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
                count_query = count_query.where(getattr(self.model, key) == value)

        # 总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)
        items = result.scalars().all()

        return items, total

    async def create(self, **kwargs) -> ModelType:
        """创建记录"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, **kwargs) -> ModelType | None:
        """更新记录"""
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key) and value is not None:
                    setattr(instance, key, value)
            await self.session.flush()
            await self.session.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        """删除记录"""
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
