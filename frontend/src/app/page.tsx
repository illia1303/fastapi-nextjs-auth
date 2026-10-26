"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

import { api, getErrorMessage } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // POST /auth/login — бекенд ставит httpOnly cookie с токеном, браузер сохранит её сам
      await api.post("/auth/login", { email, password });
      router.push("/products");
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen px-4">

      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md dark:bg-neutral-900">

        <h1 className="text-2xl font-bold text-center mb-6">Вход в систему</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">Email</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition dark:border-neutral-700 dark:bg-neutral-800"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">Пароль</label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition dark:border-neutral-700 dark:bg-neutral-800"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg dark:text-red-400 dark:bg-red-950/50">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium mt-4 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Входим..." : "Войти"}
          </button>
        </form>

        <p className="text-sm text-center text-gray-600 mt-6 dark:text-neutral-400">
          Нет аккаунта?{" "}
          <Link href="/register" className="text-blue-600 hover:underline font-medium dark:text-blue-400">
            Зарегистрироваться
          </Link>
        </p>

      </div>
    </main>
  );
}
