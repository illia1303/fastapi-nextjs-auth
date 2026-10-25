import axios from "axios";

// Адрес бекенда берётся из .env.local (NEXT_PUBLIC_API_URL), по умолчанию — локальный FastAPI
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Общий axios-клиент.
// JWT хранится в httpOnly cookie, которую ставит бекенд при логине: JavaScript её не видит
// и не хранит токен сам. withCredentials: true — браузер прикладывает эту cookie к запросам на API.
export const api = axios.create({ baseURL: API_URL, withCredentials: true });

// Типы ответов бекенда (совпадают со схемами ProductResponse / UserResponse)
export interface Product {
  id: number;
  title: string;
  price: number;
  is_active: boolean;
}

export interface User {
  id: number;
  email: string;
  is_active: boolean;
}

// Достаём понятный текст ошибки из ответа FastAPI:
// - HTTPException -> {"detail": "текст"}
// - ошибка валидации (422) -> {"detail": [{"msg": "..."}, ...]}
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "Сервер недоступен. Проверьте, что бекенд запущен.";
    }
    const detail = error.response.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((item: { msg: string }) => item.msg).join("; ");
    }
  }
  return "Что-то пошло не так. Попробуйте ещё раз.";
}

export function isUnauthorized(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 401;
}
