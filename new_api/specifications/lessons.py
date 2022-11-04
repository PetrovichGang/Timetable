from datetime import datetime

from .base import SpecificationProtocol
from new_api.schemes.lessons import DefaultLessonsScheme, ChangeLessonsScheme


class DefaultLessonsForGroupSpecification(SpecificationProtocol[DefaultLessonsScheme]):
    def __init__(self, group: str):
        self.group = group

    def is_satisfied(self, candidate: DefaultLessonsScheme) -> bool:
        return self.group == candidate.group

    def expression(self) -> dict:
        return {"group": self.group}


class ChangesLessonsByDateSpecification(SpecificationProtocol[ChangeLessonsScheme]):
    def __init__(self, date: datetime):
        self.date = date

    def is_satisfied(self, candidate: ChangeLessonsScheme) -> bool:
        return self.date == candidate.date

    def expression(self) -> dict:
        return {"date": self.date.strftime("%d.%m.%Y")}


class ChangesLessonsByPeriodOfDaysSpecification(SpecificationProtocol[ChangeLessonsScheme]):
    def __init__(self, start_at: datetime, finish_at: datetime):
        self.start_at = start_at
        self.finish_at = finish_at

    def is_satisfied(self, candidate: ChangeLessonsScheme) -> bool:
        return self.start_at <= candidate.date <= self.finish_at

    def expression(self) -> dict:
        return {
                "$expr": {
                    "$and": [
                        {
                            "$gte": [
                                {
                                    "$dateFromString": {
                                        "dateString": "$date",
                                        "format": "%d.%m.%Y"
                                    }
                                },
                                self.start_at
                            ],
                        },
                        {
                            "$lte": [
                                {
                                    "$dateFromString": {
                                        "dateString": "$date",
                                        "format": "%d.%m.%Y"
                                    }
                                },
                                self.finish_at
                            ],
                        },
                    ],
                }
            }
