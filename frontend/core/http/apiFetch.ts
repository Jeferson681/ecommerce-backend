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

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const url = `${API_URL}${path}`;
  const runtime = globalThis as typeof globalThis & {
    localStorage?: Storage;
  };

  try {
    const headers = new Headers(options.headers);
    if (!headers.has("Accept")) headers.set("Accept", "application/json");

    // Optional auth: if an access token exists, attach it by default.
    // Guard access to localStorage: some server runtimes (Turbopack) expose
    // a `localStorage` object that doesn't implement `getItem`. Check
    // that `getItem` is a function before calling it.
    if (typeof runtime.localStorage?.getItem === "function" && !headers.has("Authorization")) {
      const token = runtime.localStorage.getItem("access_token");
      if (token) headers.set("Authorization", `Bearer ${token}`);
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
