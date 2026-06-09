"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/**
 * Auth client. Access token BELLEKTE tutulur (localStorage DEĞİL — XSS riski,
 * mutlak kural). Refresh token backend tarafından httpOnly cookie'de saklanır;
 * sayfa yenilenince /auth/refresh ile yeni access alınır (sessiz oturum sürdürme).
 *
 * Cross-origin (3000→8000) cookie için tüm auth isteklerinde credentials:'include'.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
};

type AuthContextValue = {
  user: User | null;
  loading: boolean; // ilk refresh denemesi sürerken true
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function api(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include", // refresh cookie'sini gönder/al
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Access token alındıktan sonra /auth/me ile kullanıcıyı çek.
  const fetchMe = useCallback(async (token: string) => {
    const res = await api("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) setUser((await res.json()) as User);
  }, []);

  // Sayfa açılışında refresh cookie varsa sessizce oturumu kur.
  useEffect(() => {
    (async () => {
      try {
        const res = await api("/auth/refresh", { method: "POST" });
        if (res.ok) {
          const data = (await res.json()) as { access_token: string };
          setAccessToken(data.access_token);
          await fetchMe(data.access_token);
        }
      } catch {
        // refresh yoksa misafir; sorun değil.
      } finally {
        setLoading(false);
      }
    })();
  }, [fetchMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Giriş başarısız");
      }
      const data = (await res.json()) as { access_token: string };
      setAccessToken(data.access_token);
      await fetchMe(data.access_token);
    },
    [fetchMe],
  );

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const res = await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name: fullName || null }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const detail = err?.detail;
        throw new Error(typeof detail === "string" ? detail : "Kayıt başarısız");
      }
      // Kayıt sonrası otomatik giriş.
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    await api("/auth/logout", { method: "POST" }).catch(() => null);
    setAccessToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, accessToken, login, register, logout }),
    [user, loading, accessToken, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth, AuthProvider içinde kullanılmalı");
  return ctx;
}
