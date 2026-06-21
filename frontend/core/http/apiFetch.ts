import { API_URL } from "@/core/config/api";
import { ApiError } from "@/core/exceptions/ApiError";
import { buildFriendlyApiMessage } from "@/core/exceptions/userMessage";

type ApiFetchOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

async function safeReadText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

function tryParseJson(text: string): unknown {
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function getLocalStorage(): Storage | null {
  const runtime = globalThis as typeof globalThis & { localStorage?: Storage };
  if (typeof runtime.localStorage?.getItem === "function") {
    return runtime.localStorage;
  }
  return null;
}

function getAccessToken(): string | null {
  return getLocalStorage()?.getItem("access_token") ?? null;
}

function setAccessToken(token: string): void {
  getLocalStorage()?.setItem("access_token", token);
}

function clearAuth(): void {
  const ls = getLocalStorage();
  if (!ls) return;
  ls.removeItem("access_token");
  ls.removeItem("refresh_token");
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("auth_token_changed"));
  }
}

function getRefreshToken(): string | null {
  const ls = getLocalStorage();
  if (!ls) return null;
  return ls.getItem("refresh_token");
}

function setRefreshToken(token: string): void {
  getLocalStorage()?.setItem("refresh_token", token);
}

async function attemptTokenRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      clearAuth();
      return false;
    }

    const data = await res.json();
    setAccessToken(data.access_token);
    if (data.refresh_token) {
      setRefreshToken(data.refresh_token);
    }
    return true;
  } catch {
    clearAuth();
    return false;
  }
}

export { clearAuth };

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const url = `${API_URL}${path}`;

  try {
    const headers = new Headers(options.headers);
    if (!headers.has("Accept")) headers.set("Accept", "application/json");

    // Attach access token automatically
    const token = getAccessToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    let body: BodyInit | undefined;
    if (options.body !== undefined) {
      if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
      body = JSON.stringify(options.body);
    }

    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers,
        body,
        cache: "no-store",
      });
    } catch (e) {
      console.error("apiFetch: network error when fetching", url, e);
      throw new ApiError(
        "Unable to connect to the server. Please check your connection and try again.",
        0
      );
    }

    // If 401 and we have a refresh token, attempt refresh and retry once
    if (response.status === 401 && getRefreshToken()) {
      const refreshed = await attemptTokenRefresh();
      if (refreshed) {
        // Retry with new token
        const newToken = getAccessToken();
        if (newToken) {
          headers.set("Authorization", `Bearer ${newToken}`);
        }

        try {
          response = await fetch(url, {
            ...options,
            headers,
            body,
            cache: "no-store",
          });
        } catch (e) {
          console.error("apiFetch: network error on retry", url, e);
          throw new ApiError(
            "Unable to connect to the server. Please check your connection and try again.",
            0
          );
        }
      } else {
        // Refresh failed — clear auth
        clearAuth();
        throw new ApiError("Your session has expired. Please sign in again.", 401);
      }
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const text = await safeReadText(response);
    const payload = tryParseJson(text);

    if (!response.ok) {
      console.error("apiFetch: non-ok response", { url, status: response.status, text });
      const friendlyMessage = buildFriendlyApiMessage(response.status, payload);
      throw new ApiError(friendlyMessage, response.status, payload);
    }

    return payload as T;
  } catch (e) {
    console.error("apiFetch: unexpected error", { url, error: e });
    throw e;
  }
}
