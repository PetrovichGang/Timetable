from typing import Protocol, TypeVar, Iterable

T = TypeVar("T")


class SpecificationProtocol(Protocol[T]):
    def is_satisfied(self, candidate: T) -> bool:
        ...

    def expression(self) -> dict:
        ...


class _BaseOperator(SpecificationProtocol):
    def __init__(self, *specifications: SpecificationProtocol):
        self.specifications: Iterable[SpecificationProtocol] = specifications


class AND(_BaseOperator):
    def is_satisfied(self, candidate: T) -> bool:
        return all([spec.is_satisfied(candidate) for spec in self.specifications])

    def expression(self) -> dict:
        return {"$and": [spec.expression() for spec in self.specifications]}


class OR(_BaseOperator):
    def is_satisfied(self, candidate: T) -> bool:
        return any([spec.is_satisfied(candidate) for spec in self.specifications])

    def expression(self) -> dict:
        return {"$or": [spec.expression() for spec in self.specifications]}
