from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import ProductModel


class ProductAlreadyExistsError(Exception):
    pass


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int) -> ProductModel | None:
        query = select(ProductModel).where(ProductModel.id == product_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ProductModel]:
        query = select(ProductModel).order_by(ProductModel.id.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict) -> ProductModel:
        product = ProductModel(**data)
        self.session.add(product)
        try:
            await self.session.commit()
        except IntegrityError:
            # title уникальный — откатываем сессию, чтобы её можно было использовать дальше
            await self.session.rollback()
            raise ProductAlreadyExistsError(f"Товар с названием '{data['title']}' уже существует")
        await self.session.refresh(product)
        return product

    async def update(self, product: ProductModel, data: dict) -> ProductModel:
        for field, value in data.items():
            setattr(product, field, value)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ProductAlreadyExistsError(f"Товар с названием '{data.get('title')}' уже существует")
        await self.session.refresh(product)
        return product

    async def delete(self, product: ProductModel) -> None:
        await self.session.delete(product)
        await self.session.commit()