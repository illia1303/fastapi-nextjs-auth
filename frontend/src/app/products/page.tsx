"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProductCard } from "@/components/ProductCard";
import { ProductForm } from "@/components/ProductForm";
import { api, getErrorMessage, isUnauthorized, type Product, type User } from "@/lib/api";

export default function ProductsPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Сессия закончилась (нет cookie или токен истёк) — отправляем на страницу входа
  const goToLogin = useCallback(() => {
    router.replace("/");
  }, [router]);

  // Кнопка "Выйти": бекенд удаляет httpOnly cookie (сам JS удалить её не может)
  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      goToLogin();
    }
  };

  useEffect(() => {
    let cancelled = false;

    // Загружаем текущего пользователя и список товаров параллельно.
    // /auth/me заодно проверяет сессию: без валидной cookie вернёт 401.
    Promise.all([api.get<User>("/auth/me"), api.get<Product[]>("/products/")])
      .then(([me, list]) => {
        if (cancelled) return;
        setUser(me.data);
        setProducts(list.data);
      })
      .catch((err) => {
        if (cancelled) return;
        if (isUnauthorized(err)) {
          goToLogin();
          return;
        }
        setError(getErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [goToLogin]);

  // Новые товары сверху — так же сортирует бекенд
  const handleCreated = (product: Product) => setProducts((prev) => [product, ...prev]);

  const handleUpdated = (updated: Product) =>
    setProducts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));

  const handleDeleted = (id: number) => setProducts((prev) => prev.filter((p) => p.id !== id));

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">

      <header className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-neutral-100">Товары</h1>
        <div className="flex items-center gap-4">
          {user && <span className="text-sm text-gray-600 break-all dark:text-neutral-400">{user.email}</span>}
          <button
            type="button"
            onClick={logout}
            className="text-sm font-medium text-gray-700 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors dark:text-neutral-300 dark:border-neutral-700 dark:hover:bg-neutral-800"
          >
            Выйти
          </button>
        </div>
      </header>

      <ProductForm onCreated={handleCreated} onUnauthorized={goToLogin} />

      {loading && <p className="text-gray-500 dark:text-neutral-400">Загрузка...</p>}

      {error && (
        <p role="alert" className="text-red-600 bg-red-50 px-4 py-3 rounded-lg dark:text-red-400 dark:bg-red-950/50">{error}</p>
      )}

      {!loading && !error && products.length === 0 && (
        <p className="text-gray-500 text-center py-12 dark:text-neutral-400">Товаров пока нет — добавьте первый.</p>
      )}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onUpdated={handleUpdated}
            onDeleted={handleDeleted}
            onUnauthorized={goToLogin}
          />
        ))}
      </div>
    </main>
  );
}
