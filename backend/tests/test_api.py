from httpx import AsyncClient


class TestCreateProductEndpoint:
    async def test_create_product_success_returns_201(self, client: AsyncClient):
        payload = {"title": "macbook pro", "price": 2499.99}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 201

    async def test_create_product_returns_correct_json_structure(self, client: AsyncClient):
        payload = {"title": "Iphone 20", "price": 2000.00}
        response = await client.post("/products/", json=payload)

        data = response.json()

        assert "id" in data
        assert "title" in data
        assert "price" in data
        assert "is_active" in data

    async def test_create_product_returns_correct_values(self, client: AsyncClient):
        payload = {"title": "Iphone Duo", "price": 1000.00}
        response = await client.post("/products/", json=payload)

        data = response.json()

        assert data["title"] == "Iphone Duo"
        assert data["price"] == 1000.00

    async def test_create_product_id_is_integer(self, client: AsyncClient):
        payload = {"title": "Tablet", "price": 1500.00}
        response = await client.post("/products/", json=payload)

        data = response.json()

        assert isinstance(data["id"], int)
        assert data["id"] > 0

    async def test_create_product_is_active_defaults_to_true(self, client: AsyncClient):
        """Новый продукт должен быть активным по умолчанию."""
        payload = {"title": "Наушники", "price": 199.0}
        response = await client.post("/products/", json=payload)
        data = response.json()

        assert data["is_active"] is True

    # ─── Тесты валидации входных данных ──────────────────────────────────────

    async def test_create_product_empty_title_returns_422(self, client: AsyncClient):
        """
        Пустой заголовок нарушает min_length=2.
        FastAPI автоматически возвращает 422 Unprocessable Entity
        при ошибках валидации Pydantic.
        """
        payload = {"title": "", "price": 100.0}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_short_title_returns_422(self, client: AsyncClient):
        """Заголовок из 1 символа — нарушение min_length=2."""
        payload = {"title": "A", "price": 100.0}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_long_title_returns_422(self, client: AsyncClient):
        """Заголовок длиннее 100 символов — нарушение max_length=100."""
        payload = {"title": "X" * 101, "price": 100.0}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_zero_price_returns_422(self, client: AsyncClient):
        """Цена 0 нарушает gt=0 в Pydantic схеме."""
        payload = {"title": "Бесплатно", "price": 0}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_negative_price_returns_422(self, client: AsyncClient):
        """Отрицательная цена нарушает gt=0."""
        payload = {"title": "Товар", "price": -100.0}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_missing_title_returns_422(self, client: AsyncClient):
        """Отсутствие обязательного поля title."""
        payload = {"price": 100.0}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_missing_price_returns_422(self, client: AsyncClient):
        """Отсутствие обязательного поля price."""
        payload = {"title": "Товар без цены"}
        response = await client.post("/products/", json=payload)
        assert response.status_code == 422

    async def test_create_product_empty_body_returns_422(self, client: AsyncClient):
        """Полностью пустое тело запроса."""
        response = await client.post("/products/", json={})
        assert response.status_code == 422

    # ─── Тест бизнес-логики (через API) ──────────────────────────────────────

    async def test_create_product_price_below_business_minimum_returns_400(
            self, client: AsyncClient
    ):
        """
        Цена 0.5 проходит Pydantic (> 0), но нарушает бизнес-правило (< 1.0).
        Сервис бросает ValueError, роутер перехватывает и возвращает 400 Bad Request.

        Это тест граничного взаимодействия между слоями!
        """
        payload = {"title": "Копеечный товар", "price": 0.5}
        response = await client.post("/products/", json=payload)

        assert response.status_code == 400
        # Проверяем что сообщение об ошибке в теле ответа
        assert "detail" in response.json()

    async def test_create_product_422_response_has_detail_field(self, client: AsyncClient):
        """
        Ответы с ошибками валидации FastAPI всегда содержат поле 'detail'
        с описанием что именно не так.
        """
        payload = {"title": "X", "price": 100.0}  # слишком короткий title
        response = await client.post("/products/", json=payload)

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)  # список ошибок валидации

    # ─── Тест идемпотентности и множественных запросов ──────────────────────

    async def test_multiple_products_get_unique_ids(self, client: AsyncClient):
        """
        Создание нескольких продуктов — каждый получает уникальный id.
        Проверяем что автоинкремент БД работает корректно.
        """
        response1 = await client.post("/products/", json={"title": "Первый", "price": 10.0})
        response2 = await client.post("/products/", json={"title": "Второй", "price": 20.0})
        response3 = await client.post("/products/", json={"title": "Третий", "price": 30.0})

        id1 = response1.json()["id"]
        id2 = response2.json()["id"]
        id3 = response3.json()["id"]

        # Все id уникальны
        assert len({id1, id2, id3}) == 3

    # ─── Тест уникальности названия ──────────────────────────────────────────

    async def test_create_product_duplicate_title_returns_409(self, client: AsyncClient):
        """
        title уникальный в БД. Повторное создание товара с тем же названием
        должно возвращать 409 Conflict, а не 500.
        """
        payload = {"title": "Дубликат", "price": 100.0}
        first = await client.post("/products/", json=payload)
        second = await client.post("/products/", json={"title": "Дубликат", "price": 200.0})

        assert first.status_code == 201
        assert second.status_code == 409
        assert "Дубликат" in second.json()["detail"]

    async def test_create_product_without_auth_returns_401(self, anon_client: AsyncClient):
        response = await anon_client.post("/products/", json={"title": "Без токена", "price": 10.0})
        assert response.status_code == 401


class TestListProductsEndpoint:
    async def test_list_is_public_and_contains_created(self, client: AsyncClient, anon_client: AsyncClient):
        created = (await client.post("/products/", json={"title": "Для списка", "price": 50.0})).json()

        response = await anon_client.get("/products/")

        assert response.status_code == 200
        assert any(p["id"] == created["id"] for p in response.json())

    async def test_list_newest_first(self, client: AsyncClient):
        first = (await client.post("/products/", json={"title": "Старый", "price": 10.0})).json()
        second = (await client.post("/products/", json={"title": "Новый", "price": 10.0})).json()

        ids = [p["id"] for p in (await client.get("/products/")).json()]

        assert ids.index(second["id"]) < ids.index(first["id"])


class TestUpdateProductEndpoint:
    async def test_update_fields(self, client: AsyncClient):
        product = (await client.post("/products/", json={"title": "До правки", "price": 10.0})).json()

        response = await client.patch(
            f"/products/{product['id']}",
            json={"title": "После правки", "price": 20.0, "is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "После правки"
        assert data["price"] == 20.0
        assert data["is_active"] is False

    async def test_partial_update_keeps_other_fields(self, client: AsyncClient):
        product = (await client.post("/products/", json={"title": "Частично", "price": 10.0})).json()

        data = (await client.patch(f"/products/{product['id']}", json={"price": 15.0})).json()

        assert data["title"] == "Частично"
        assert data["price"] == 15.0

    async def test_update_missing_product_returns_404(self, client: AsyncClient):
        response = await client.patch("/products/999999", json={"price": 15.0})
        assert response.status_code == 404

    async def test_update_to_existing_title_returns_409(self, client: AsyncClient):
        await client.post("/products/", json={"title": "Занято", "price": 10.0})
        other = (await client.post("/products/", json={"title": "Свободно", "price": 10.0})).json()

        response = await client.patch(f"/products/{other['id']}", json={"title": "Занято"})

        assert response.status_code == 409

    async def test_update_price_below_minimum_returns_400(self, client: AsyncClient):
        product = (await client.post("/products/", json={"title": "Цена вниз", "price": 10.0})).json()
        response = await client.patch(f"/products/{product['id']}", json={"price": 0.5})
        assert response.status_code == 400

    async def test_update_without_auth_returns_401(self, anon_client: AsyncClient):
        response = await anon_client.patch("/products/1", json={"price": 15.0})
        assert response.status_code == 401


class TestDeleteProductEndpoint:
    async def test_delete_then_404(self, client: AsyncClient):
        product = (await client.post("/products/", json={"title": "Удаляемый", "price": 10.0})).json()

        first = await client.delete(f"/products/{product['id']}")
        second = await client.delete(f"/products/{product['id']}")

        assert first.status_code == 204
        assert second.status_code == 404

    async def test_delete_without_auth_returns_401(self, anon_client: AsyncClient):
        response = await anon_client.delete("/products/1")
        assert response.status_code == 401



