"""
test_services.py — тесты бизнес-логики (сервисного слоя).

Зачем тестировать сервисы отдельно?
- Сервис содержит бизнес-логику (правила, которые не зависят от БД)
- Используем Mock (заглушку) вместо реального репозитория
- Тест максимально быстрый и изолированный

Паттерн: Unit-тест с Mock (имитация зависимостей)
- AsyncMock — заглушка для async-методов
- Мы проверяем поведение сервиса, не репозитория
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.product import ProductNotFoundError, ProductService
from app.schemas.product import ProductCreate, ProductUpdate


class TestProductService:
    """Тесты ProductService с мок-репозиторием."""

    def setup_method(self):
        """
        setup_method вызывается перед каждым тестом в классе.
        Создаём мок-репозиторий и внедряем его в сервис.

        AsyncMock — специальный мок для async-методов.
        Когда код делает `await mock.create(...)`, он работает как настоящий async вызов.
        """
        self.mock_repo = MagicMock()
        self.mock_repo.create = AsyncMock()
        self.service = ProductService(repo=self.mock_repo)

    async def test_add_product_success(self):
        """
        Проверяем успешный сценарий: сервис должен вызвать repo.create()
        и вернуть то, что вернул репозиторий.
        """
        # Arrange (подготовка)
        payload = ProductCreate(title="Ноутбук", price=1500.0)

        # Настраиваем что вернёт мок-репозиторий
        fake_product = MagicMock()
        fake_product.id = 1
        fake_product.title = "Ноутбук"
        fake_product.price = 1500.0
        fake_product.is_active = True
        self.mock_repo.create.return_value = fake_product

        # Act (действие)
        result = await self.service.add_product(payload)

        # Assert (проверка)
        assert result == fake_product
        # Убеждаемся что repo.create был вызван ровно один раз
        self.mock_repo.create.assert_called_once()

    async def test_add_product_calls_repo_with_correct_data(self):
        """
        Проверяем что сервис передаёт в репозиторий правильные данные.
        Это гарантирует, что model_dump() вызывается корректно.
        """
        payload = ProductCreate(title="Телефон", price=999.0)

        fake_product = MagicMock(id=2, title="Телефон", price=999.0, is_active=True)
        self.mock_repo.create.return_value = fake_product

        await self.service.add_product(payload)

        # Проверяем аргументы вызова репозитория
        call_args = self.mock_repo.create.call_args
        assert call_args[0][0] == {"title": "Телефон", "price": 999.0}

    async def test_add_product_price_below_minimum_raises_value_error(self):
        """
        Бизнес-правило: цена ниже $1.00 недопустима.
        Сервис должен бросить ValueError ДО обращения к БД.

        Примечание: Pydantic уже отсекает price <= 0, но сервис
        имеет дополнительное правило: price >= 1.0.
        """
        # Цена 0.5 — проходит Pydantic (> 0), но не проходит бизнес-проверку
        payload = ProductCreate(title="Дешёвый товар", price=0.5)

        with pytest.raises(ValueError) as exc_info:
            await self.service.add_product(payload)

        # Проверяем текст ошибки (полезно для клиентов API)
        assert "1.00" in str(exc_info.value)

        # Самое важное: репозиторий НЕ должен был вызываться
        self.mock_repo.create.assert_not_called()

    async def test_add_product_price_exactly_one_dollar(self):
        """Граничный случай: цена ровно $1.00 — должна быть принята."""
        payload = ProductCreate(title="Минимальный товар", price=1.0)

        fake_product = MagicMock(id=3, title="Минимальный товар", price=1.0, is_active=True)
        self.mock_repo.create.return_value = fake_product

        # Не должно быть исключений
        result = await self.service.add_product(payload)
        assert result == fake_product

    async def test_add_product_price_just_below_one_dollar(self):
        """Граничный случай: цена $0.99 — должна быть отклонена."""
        payload = ProductCreate(title="Товар", price=0.99)

        with pytest.raises(ValueError):
            await self.service.add_product(payload)

        self.mock_repo.create.assert_not_called()

    async def test_update_missing_product_raises_not_found(self):
        self.mock_repo.get_by_id = AsyncMock(return_value=None)
        self.mock_repo.update = AsyncMock()

        with pytest.raises(ProductNotFoundError):
            await self.service.update_product(1, ProductUpdate(price=10.0))

        self.mock_repo.update.assert_not_called()

    async def test_update_price_below_minimum_raises_value_error(self):
        self.mock_repo.get_by_id = AsyncMock()
        self.mock_repo.update = AsyncMock()

        with pytest.raises(ValueError):
            await self.service.update_product(1, ProductUpdate(price=0.5))

        self.mock_repo.update.assert_not_called()

    async def test_update_passes_only_sent_fields(self):
        product = MagicMock()
        self.mock_repo.get_by_id = AsyncMock(return_value=product)
        self.mock_repo.update = AsyncMock(return_value=product)

        await self.service.update_product(1, ProductUpdate(is_active=False))

        self.mock_repo.update.assert_called_once_with(product, {"is_active": False})

    async def test_delete_missing_product_raises_not_found(self):
        self.mock_repo.get_by_id = AsyncMock(return_value=None)
        self.mock_repo.delete = AsyncMock()

        with pytest.raises(ProductNotFoundError):
            await self.service.delete_product(1)

        self.mock_repo.delete.assert_not_called()
