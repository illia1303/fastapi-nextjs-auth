// Карточка теперь интерактивная (кнопки, useState), поэтому это клиентский компонент
"use client";

// Подключаем React, чтобы использовать тип React.FC (Function Component), и хук useState
import React, { useState } from "react";

// api — axios-клиент; Product — тип товара { id, title, price, is_active }
import { api, getErrorMessage, isUnauthorized, type Product } from "@/lib/api";

// interface описывает, какие данные (props) компонент ждёт снаружи.
// TypeScript будет подсвечивать ошибку, если передать что-то не то.
interface ProductProps {
  product: Product;                         // сам товар
  onUpdated: (product: Product) => void;    // товар изменён на сервере
  onDeleted: (id: number) => void;          // товар удалён на сервере
  onUnauthorized: () => void;               // токен просрочен
}

// Объявляем компонент ProductCard.
// ({ product, ... }) — деструктуризация: достаём props сразу в аргументах.
export const ProductCard: React.FC<ProductProps> = ({ product, onUpdated, onDeleted, onUnauthorized }) => {
  // busy — идёт запрос (кнопки блокируются); error — текст ошибки под карточкой
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // editing — открыт ли режим изменения цены; price — что введено в поле (строкой, как в ProductForm)
  const [editing, setEditing] = useState(false);
  const [price, setPrice] = useState("");

  // Общая обёртка для запросов карточки: блокировка кнопок + обработка ошибок
  const run = async (request: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await request();
    } catch (err) {
      if (isUnauthorized(err)) {
        onUnauthorized();
        return;
      }
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  // PATCH /products/{id} — переключаем активность товара
  const toggleActive = () =>
    run(async () => {
      const { data } = await api.patch<Product>(`/products/${product.id}`, { is_active: !product.is_active });
      onUpdated(data);
    });

  // Открываем редактирование: в поле подставляем текущую цену товара
  const startEdit = () => {
    setPrice(String(product.price));
    setError(null);
    setEditing(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setError(null);
  };

  // PATCH /products/{id} — отправляем только цену, остальные поля бекенд не тронет.
  // Режим редактирования закрываем только при успехе: при ошибке введённое значение остаётся в поле
  const savePrice = (e: React.FormEvent) => {
    e.preventDefault();
    run(async () => {
      const { data } = await api.patch<Product>(`/products/${product.id}`, { price: parseFloat(price) });
      onUpdated(data);
      setEditing(false);
    });
  };

  // DELETE /products/{id} — удаляем после подтверждения
  const remove = () => {
    if (!confirm(`Удалить товар «${product.title}»?`)) return;
    run(async () => {
      await api.delete(`/products/${product.id}`);
      onDeleted(product.id);
    });
  };

  // return — то, что компонент отрисует на странице (JSX)
  return (
    // Внешний контейнер карточки. Классы Tailwind CSS:
    // bg-white — белый фон; p-6 — внутренние отступы со всех сторон
    // rounded-2xl — сильно скруглённые углы; shadow-sm — лёгкая тень
    // border border-gray-100 — тонкая светло-серая рамка
    // hover:shadow-lg — при наведении тень становится больше
    // transition-all duration-300 — плавная анимация изменений за 300 мс
    // group — позволяет дочерним элементам реагировать на hover родителя
    // dark:... — те же стили для тёмной темы ОС (тёмный фон и рамка)
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 group dark:bg-neutral-900 dark:border-neutral-800">

      {/* Верхняя строка с бейджем "Товар" */}
      {/* flex — включаем flexbox; justify-between — элементы по краям */}
      {/* items-start — выравнивание по верху; mb-4 — отступ снизу */}
      <div className="flex justify-between items-start mb-4">

        {/* Небольшая метка-бейдж */}
        {/* text-xs — мелкий текст; font-semibold — полужирный */}
        {/* uppercase — ЗАГЛАВНЫЕ буквы; tracking-wider — шире расстояние между буквами */}
        {/* text-blue-600 bg-blue-50 — синий текст на светло-синем фоне */}
        {/* px-2.5 py-1 — отступы по горизонтали и вертикали; rounded-md — скругление */}
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/50 px-2.5 py-1 rounded-md">
          Товар
        </span>
      </div>

      {/* Заголовок карточки — название товара */}
      {/* text-xl — крупный текст; font-bold — жирный; text-gray-900 — почти чёрный */}
      {/* mb-2 — отступ снизу; leading-tight — плотная высота строки */}
      {/* {product.title} — в фигурных скобках вставляем JS-значение из props */}
      <h2 className="text-xl font-bold text-gray-900 mb-2 leading-tight dark:text-neutral-100">{product.title}</h2>

      {/* Нижний блок: цена слева, статус справа */}
      {/* justify-between — цена и статус разъезжаются по краям */}
      {/* items-end — выравнивание по нижнему краю; mt-6 — отступ сверху */}
      {/* gap-4 — промежуток между ценой и статусом, когда открыта форма редактирования */}
      <div className="flex justify-between items-end gap-4 mt-6">

        {/* Левая часть — цена или форма её изменения */}
        {editing ? (
          // flex-1 — форма занимает всё место слева от статуса
          <form onSubmit={savePrice} className="flex-1">
            {/* id с product.id — карточек на странице много, id должны быть уникальными */}
            <label htmlFor={`product-price-${product.id}`} className="block text-sm text-gray-500 mb-1 dark:text-neutral-400">
              Новая цена, ₽
            </label>
            <input
              id={`product-price-${product.id}`}
              type="number"
              required
              min="1"         // то же правило, что при создании и на бекенде
              step="0.01"
              autoFocus       // курсор сразу в поле
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              onKeyDown={(e) => e.key === "Escape" && cancelEdit()} // Esc — отмена
              className="w-full px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition dark:border-neutral-700 dark:bg-neutral-800"
            />
            <div className="flex gap-2 mt-2">
              <button
                type="submit"
                disabled={busy}
                className="text-sm font-medium bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60"
              >
                {busy ? "Сохраняем..." : "Сохранить"}
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                disabled={busy}
                className="text-sm font-medium text-gray-700 border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-60 dark:text-neutral-300 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                Отмена
              </button>
            </div>
          </form>
        ) : (
          <div>
            {/* Подпись "Цена" и ссылка-кнопка "Изменить" в одну строку */}
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm text-gray-500 dark:text-neutral-400">Цена</p>
              <button
                type="button"
                onClick={startEdit}
                disabled={busy}
                className="text-sm text-blue-600 hover:underline disabled:opacity-60 dark:text-blue-400"
              >
                Изменить
              </button>
            </div>

            {/* Само значение цены: крупно и очень жирно (font-black) */}
            {/* toLocaleString("ru-RU") форматирует число по-русски: 1500000 → "1 500 000" */}
            {/* После числа добавляем символ рубля */}
            <p className="text-2xl font-black text-gray-900 dark:text-neutral-100">{product.price.toLocaleString("ru-RU")} ₽</p>
          </div>
        )}

        {/* Правая часть — статус товара. text-right — выравнивание текста вправо */}
        <div className="text-right">

          {/* Условный рендеринг (тернарный оператор): условие ? если_true : если_false */}
          {product.is_active ? (
            // Если товар активен — показываем зелёный бейдж
            // inline-flex — блок по размеру содержимого, внутри flex
            // items-center gap-1.5 — центрируем и делаем промежуток между точкой и текстом
            // bg-green-50 text-green-700 — зелёные цвета; rounded-full — полностью круглые края
            <span className="inline-flex items-center gap-1.5 bg-green-50 text-green-700 text-sm dark:bg-green-950/50 dark:text-green-400 px-3 py-1.5 rounded-full font-medium">
              {/* Маленькая зелёная точка-индикатор: w-1.5 h-1.5 — размер 6×6 px */}
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Активен
            </span>
          ) : (
            // Иначе (is_active === false) — красный бейдж с теми же стилями, но красными цветами
            <span className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 text-sm dark:bg-red-950/50 dark:text-red-400 px-3 py-1.5 rounded-full font-medium">
              {/* Красная точка-индикатор */}
              <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              Неактивен
            </span>
          )}
        </div>
      </div>

      {/* Кнопки управления товаром. border-t — разделительная линия сверху */}
      <div className="flex gap-2 mt-6 pt-4 border-t border-gray-100 dark:border-neutral-800">
        <button
          type="button"
          onClick={toggleActive}
          disabled={busy}
          className="flex-1 text-sm font-medium text-gray-700 border border-gray-300 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-60 dark:text-neutral-300 dark:border-neutral-700 dark:hover:bg-neutral-800"
        >
          {product.is_active ? "Скрыть" : "Показать"}
        </button>
        <button
          type="button"
          onClick={remove}
          disabled={busy}
          className="flex-1 text-sm font-medium text-red-600 border border-red-200 px-3 py-2 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-60 dark:text-red-400 dark:border-red-900 dark:hover:bg-red-950/50"
        >
          Удалить
        </button>
      </div>

      {/* Ошибка запроса — показываем только если она есть */}
      {error && <p role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
};