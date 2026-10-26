// В Next.js (App Router) без этой директивы будет ошибка: useState работает только на клиенте.
"use client";

// Подключаем React (для типа React.FormEvent) и хук useState для хранения данных формы
import React, { useState } from "react";

// api — axios-клиент с адресом бекенда и токеном; Product — тип ответа сервера
import { api, getErrorMessage, isUnauthorized, type Product } from "@/lib/api";

// Props: что делать после успешного создания товара и при протухшем токене
interface ProductFormProps {
  onCreated: (product: Product) => void;
  onUnauthorized: () => void;
}

export const ProductForm: React.FC<ProductFormProps> = ({ onCreated, onUnauthorized }) => {
  // useState возвращает пару: [текущее значение, функция для его изменения]
  // title — текст из поля "Название", начальное значение — пустая строка
  const [title, setTitle] = useState("");

  // price — значение из поля "Цена". Хранится как строка, потому что
  // input всегда отдаёт value строкой, даже если type="number"
  const [price, setPrice] = useState("");

  // error — текст ошибки от сервера (например, "товар уже существует"), null — ошибки нет
  const [error, setError] = useState<string | null>(null);

  // loading — пока запрос идёт, блокируем кнопку, чтобы не отправить товар дважды
  const [loading, setLoading] = useState(false);

  // Функция-обработчик отправки формы.
  // e: React.FormEvent — тип события отправки формы.
  const handleSubmit = async (e: React.FormEvent) => {
    // Отменяем стандартное поведение браузера: по умолчанию форма
    // перезагружает страницу при отправке. Нам это не нужно.
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // POST /products/ — бекенд вернёт созданный товар с id и is_active
      const { data } = await api.post<Product>("/products/", {
        title,                    // сокращённая запись title: title
        price: parseFloat(price)  // превращаем строку "2500.50" в число 2500.5
      });

      // Сообщаем странице о новом товаре — она добавит его в список
      onCreated(data);

      // Очищаем поля: ставим пустые строки в состояние,
      // а input'ы обновятся сами, т.к. привязаны к state через value
      setTitle("");
      setPrice("");
    } catch (err) {
      // 401 — токен просрочен: страница разлогинит пользователя
      if (isUnauthorized(err)) {
        onUnauthorized();
        return;
      }
      // 409 (дубль), 400 (цена ниже минимума), 422 (валидация) — показываем текст под формой
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    // Внешняя карточка: белый фон, отступы, скругление, тень, рамка, отступ снизу (mb-8)
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-8 dark:bg-neutral-900 dark:border-neutral-800">

      {/* Заголовок формы: крупный жирный текст с отступом снизу */}
      <h2 className="text-xl font-bold text-gray-900 mb-4 dark:text-neutral-100">Добавить новый товар</h2>

      {/* Тег form. onSubmit срабатывает при нажатии кнопки submit или Enter в поле.
          flex-col — на мобильных поля идут столбиком;
          md:flex-row — на экранах от 768px и шире они выстраиваются в строку;
          gap-4 — расстояние между блоками */}
      <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4">

        {/* Блок поля "Название". flex-1 — занимает равную долю ширины */}
        <div className="flex-1">
          {/* Подпись над полем: htmlFor связывает её с input по id */}
          <label htmlFor="product-title" className="block text-sm font-medium text-gray-700 mb-1 dark:text-neutral-300">Название товара</label>

          <input
            id="product-title"
            type="text"        // обычное текстовое поле
            required           // браузер не даст отправить форму, если поле пустое
            minLength={2}      // минимум 2 символа (проверка браузером)
            maxLength={100}    // максимум 100 символов, больше ввести нельзя

            // "Контролируемый" input: его значение всегда берётся из state
            value={title}

            // При каждом нажатии клавиши обновляем state новым текстом из поля.
            onChange={(e) => setTitle(e.target.value)}

            // Серая подсказка внутри пустого поля
            placeholder="Например, MacBook Pro"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition dark:border-neutral-700 dark:bg-neutral-800"
          />
        </div>

        {/* Блок поля "Цена", устроен так же, как "Название" */}
        <div className="flex-1">
          <label htmlFor="product-price" className="block text-sm font-medium text-gray-700 mb-1 dark:text-neutral-300">Цена, ₽</label>

          <input
            id="product-price"
            type="number"   // поле только для чисел, на телефоне откроется цифровая клавиатура
            required        // обязательное поле
            min="1"         // минимальное значение — 1 (то же правило проверяет бекенд)
            step="0.01"     // шаг 0.01, т.е. разрешены копейки

            value={price}                              // значение берётся из state
            onChange={(e) => setPrice(e.target.value)} // записываем введённое в state (как строку)
            placeholder="Например, 2500"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition dark:border-neutral-700 dark:bg-neutral-800"
          />
        </div>

        {/* Блок с кнопкой. items-end прижимает кнопку к низу,
            чтобы она была на одной линии с полями ввода, а не с подписями */}
        <div className="flex items-end">
          <button
            type="submit"       // нажатие вызывает onSubmit у формы
            disabled={loading}  // пока идёт запрос — кнопка неактивна
            // h-[42px] — фиксированная высота, равная высоте input'ов
            className="w-full md:w-auto bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium h-[42px] disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Добавляем..." : "Добавить"}
          </button>
        </div>
      </form>

      {/* Ошибка от сервера — показываем только если она есть */}
      {error && (
        <p role="alert" className="mt-4 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg dark:text-red-400 dark:bg-red-950/50">{error}</p>
      )}
    </div>
  );
};
