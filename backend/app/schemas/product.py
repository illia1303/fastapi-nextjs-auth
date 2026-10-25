from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    price: float = Field(..., gt=0)

class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=100)
    price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None

class ProductResponse(BaseModel):
    id: int
    title: str
    price: float
    is_active: bool

    model_config = {"from_attributes": True}