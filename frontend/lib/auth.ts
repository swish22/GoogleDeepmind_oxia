export type TokenBundle = {
  access_token: string;
  token_type: "bearer" | string;
};

const TOKEN_KEY = "oxia_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(TOKEN_KEY);
  if (raw == null) return null;
  const t = raw.trim();
  return t.length ? t : null;
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  const t = token.trim();
  if (!t) {
    window.localStorage.removeItem(TOKEN_KEY);
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, t);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

