import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.product import ProductAlreadyExistsError, ProductRepository


class TestProductRepository:
    async def test_create_product_returns_model(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)
        data = {"title": "test", "price": 100.00}
        product = await repo.create(data)

        assert product.id is not None
        assert product.title == "test"
        assert product.price == 100.00
        assert product.is_active is True

    async def test_create_product_assigns_incremental_id(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)
        product1 = await repo.create({"title": "test2", "price": 100.00})
        product2 = await repo.create({"title": "test3", "price": 200.00})

        assert product1.id != product2.id

    async def test_get_by_id_existing_product(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)

        created = await repo.create({"title": "test256", "price": 1000.00})
        found = await repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == "test256"

    async def test_get_by_id_non_existing_product(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)
        found = await repo.get_by_id(0)

        assert found is None

    async def test_create_stores_data_persistently(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)

        created = await repo.create({"title": "test33", "price": 12000.00})
        retrieved = await repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.price == 12000.00

    async def test_create_duplicate_title_raises_already_exists(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)
        await repo.create({"title": "dup-repo", "price": 100.00})

        with pytest.raises(ProductAlreadyExistsError):
            await repo.create({"title": "dup-repo", "price": 200.00})

    async def test_session_usable_after_duplicate(self, db_session: AsyncSession):
        repo = ProductRepository(session=db_session)
        await repo.create({"title": "dup-repo-2", "price": 100.00})

        with pytest.raises(ProductAlreadyExistsError):
            await repo.create({"title": "dup-repo-2", "price": 200.00})

        # после rollback сессия не сломана — следующая вставка проходит
        product = await repo.create({"title": "after-dup", "price": 300.00})
        assert product.id is not None

