from typing import (
    Generic,
    Optional,
    Protocol,
    Type,
    TypeVar, List,
)

from beanie.odm.operators.update.general import Set
from pydantic import BaseModel, parse_obj_as

from new_api.specifications.base import SpecificationProtocol

M = TypeVar("M", bound=BaseModel)
S = TypeVar("S", bound=BaseModel)


class BaseRepositoryProtocol(Protocol[M, S]):
    model: Type[M]
    scheme: Type[S]

    async def get_or_none(self, specification: SpecificationProtocol) -> Optional[S]:
        ...  # pragma: no cover

    async def create(self, data: S) -> S:
        ...  # pragma: no cover

    async def update(self, data: S) -> None:
        ...  # pragma: no cover

    async def delete(self, data: S) -> None:
        ...  # pragma: no cover

    async def delete_all(self) -> None:
        ...  # pragma: no cover

    async def all(self, specification: Optional[SpecificationProtocol]) -> List[S]:
        ...  # pragma: no cover


class BaseRepository(BaseRepositoryProtocol, Generic[M, S]):
    async def get_or_none(self, specification: SpecificationProtocol) -> Optional[S]:
        object = await self.model.find_one(specification.expression())
        if object is None:
            return None
        return self.scheme.parse_obj(object)

    async def create(self, data: S) -> S:
        object = self.model(**data.dict(exclude_none=True))
        await object.create()
        return self.scheme.parse_obj(object)

    async def update(self, data: S) -> None:
        object = await self.model.get(data.id)
        if object is None:
            return None
        await object.update(
            Set(
                data.dict(exclude={"id"}, exclude_unset=True)
            )
        )

    async def delete(self, data: S) -> None:
        object = await self.model.get(data.id)
        if object:
            await object.delete()

    async def delete_all(self) -> None:
        await self.model.delete_all()

    async def all(self, specification: Optional[SpecificationProtocol] = None) -> List[S]:
        if specification is None:
            result = await self.model.find_all().to_list()
        else:
            result = await self.model.find_all(specification.expression()).to_list()
        return parse_obj_as(List[S], result)
