from typing import (
    Generic,
    Optional,
    Protocol,
    Type,
    TypeVar, List,
)

from beanie.odm.operators.update.general import Set
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class BaseRepositoryProtocol(Protocol[M]):
    model: Type[M]

    async def get_or_none(self, **statement) -> Optional[M]:
        ...  # pragma: no cover

    async def create(self, data: M) -> M:
        ...  # pragma: no cover

    async def update(self, data: M) -> None:
        ...  # pragma: no cover

    async def delete(self, data: M) -> None:
        ...  # pragma: no cover

    async def all(self) -> List[M]:
        ...  # pragma: no cover


class BaseRepository(BaseRepositoryProtocol, Generic[M]):
    async def get_or_none(self, **statement) -> Optional[M]:
        object = await self.model.find_one(statement)
        if object is None:
            return None
        return object

    async def create(self, data: M) -> M:
        object = self.model(**data.dict(exclude_none=True))
        await object.create()
        return object

    async def update(self, data: M) -> None:
        object = await self.model.get(data.id)
        if object is None:
            return None
        await object.update(
            Set(
                data.dict(exclude={"id"}, exclude_unset=True)
            )
        )

    async def delete(self, data: M) -> None:
        object = await self.model.get(data.id)
        if object:
            await object.delete()

    async def all(self) -> List[M]:
        return await self.model.find_all().to_list()
