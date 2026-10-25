from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.product import ProductModel
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate

MIN_PRICE = 1.0


class ProductNotFoundError(Exception):
    pass


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    @staticmethod
    def _check_price(price: float) -> None:
        # Пример бизнес-логики: проверка цены
        if price < MIN_PRICE:
            raise ValueError("Минимальная цена товара — 1.00 ₽")

    async def add_product(self, payload: ProductCreate):
        self._check_price(payload.price)
        return await self.repo.create(payload.model_dump())

    async def list_products(self) -> list[ProductModel]:
        return await self.repo.list_all()

    async def _get_or_raise(self, product_id: int) -> ProductModel:
        product = await self.repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(f"Товар с id={product_id} не найден")
        return product

    async def update_product(self, product_id: int, payload: ProductUpdate) -> ProductModel:
        # exclude_unset — обновляем только те поля, которые клиент реально прислал
        data = payload.model_dump(exclude_unset=True, exclude_none=True)
        if "price" in data:
            self._check_price(data["price"])
        product = await self._get_or_raise(product_id)
        if not data:
            return product
        return await self.repo.update(product, data)

    async def delete_product(self, product_id: int) -> None:
        product = await self._get_or_raise(product_id)
        await self.repo.delete(product)


def get_product_service(session: AsyncSession = Depends(get_async_session)) -> ProductService:
    repo = ProductRepository(session)
    return ProductService(repo)
