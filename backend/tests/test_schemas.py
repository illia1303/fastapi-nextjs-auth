import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate, ProductResponse


class TestProductCreateSchema:
    def test_valid_product(self):
        """Корректные данные должны создавать схему без ошибок."""
        product = ProductCreate(title="Ноутбук Apple M3", price=1299.99)
        assert product.title == "Ноутбук Apple M3"
        assert product.price == 1299.99

    def test_title_too_short(self):
        """Заголовок меньше 2 символов — ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(title="A", price=100.0)
        # Проверяем что ошибка именно по полю title
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_title_too_long(self):
        """Заголовок больше 100 символов — ValidationError."""
        long_title = "A" * 101
        with pytest.raises(ValidationError):
            ProductCreate(title=long_title, price=100.0)

    def test_price_zero(self):
        """Цена равная 0 — ValidationError (нужно gt=0)."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(title="Товар", price=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("price",) for e in errors)

    def test_price_negative(self):
        """Отрицательная цена — ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreate(title="Товар", price=-50.0)

    def test_missing_title(self):
        """Отсутствие обязательного поля title — ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreate(price=100.0)

    def test_missing_price(self):
        """Отсутствие обязательного поля price — ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreate(title="Товар")

    def test_price_minimum_valid(self):
        """Минимально допустимая цена (чуть больше 0)."""
        product = ProductCreate(title="Дешёвый товар", price=0.01)
        assert product.price == 0.01

    def test_model_dump(self):
        """model_dump() возвращает корректный словарь для передачи в репозиторий."""
        product = ProductCreate(title="Тест", price=99.9)
        data = product.model_dump()
        assert data == {"title": "Тест", "price": 99.9}


class TestProductResponseSchema:
    def test_from_dict(self):
        """Схема создаётся из словаря (имитация ORM-объекта)."""
        response = ProductResponse(id=1, title="Телефон", price=799.0, is_active=True)
        assert response.id == 1
        assert response.is_active is True

    def test_from_orm_like_object(self):
        """
        model_config = {'from_attributes': True} — схема умеет читать атрибуты объекта.
        Имитируем поведение SQLAlchemy-модели через простой класс.
        """

        class FakeOrmObject:
            id = 5
            title = "ORM Product"
            price = 250.0
            is_active = False

        response = ProductResponse.model_validate(FakeOrmObject())
        assert response.id == 5
        assert response.title == "ORM Product"
        assert response.is_active is False