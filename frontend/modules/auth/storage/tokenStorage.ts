const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EVENT = "auth_token_changed";

type Listener = () => void;

function notify(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(TOKEN_EVENT));
}

/**
 * Decode JWT payload without verifying signature.
 * Extracts the `exp` claim for expiration checking.
 */
function decodeTokenPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const payload = decodeTokenPayload(token);
  if (!payload) return true;
  const exp = payload.exp as number | undefined;
  if (!exp) return true;
  // Add 10s buffer to account for clock skew
  return Date.now() >= (exp * 1000) - 10000;
}

export const tokenStorage = {
  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) return null;
    // If token is expired, clear it and return null
    if (isTokenExpired(token)) {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY);
      return null;
    }
    return token;
  },

  subscribe(listener: Listener): () => void {
    if (typeof window === "undefined") return () => undefined;

    const onEvent = () => listener();
    window.addEventListener(TOKEN_EVENT, onEvent);
    window.addEventListener("storage", onEvent);

    return () => {
      window.removeEventListener(TOKEN_EVENT, onEvent);
      window.removeEventListener("storage", onEvent);
    };
  },

  setAccessToken(token: string): void {
    if (typeof window === "undefined") return;
    // Validate token structure before storing
    if (!decodeTokenPayload(token)) {
      console.warn("tokenStorage: invalid token format, not storing");
      return;
    }
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
    notify();
  },

  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setRefreshToken(token: string): void {
    if (typeof window === "undefined") return;
    if (!decodeTokenPayload(token)) {
      console.warn("tokenStorage: invalid token format, not storing");
      return;
    }
    window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
    notify();
  },

  setTokens(accessToken: string, refreshToken: string): void {
    this.setAccessToken(accessToken);
    this.setRefreshToken(refreshToken);
  },

  clear(): void {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    notify();
  },
};
