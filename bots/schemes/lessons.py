from typing import Optional, List

from pydantic import BaseModel, AnyHttpUrl, Field


class ChangeBlock(BaseModel):
    text: str
    images: Optional[List[AnyHttpUrl]] = Field(default=list)
