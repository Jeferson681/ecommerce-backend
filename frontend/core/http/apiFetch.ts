import { API_URL } from "@/core/config/api";
import { ApiError } from "@/core/exceptions/ApiError";

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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const url = `${API_URL}${path}`;

  const headers = new Headers(options.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");

  // Optional auth: if an access token exists, attach it by default.
  if (typeof window !== "undefined" && !headers.has("Authorization")) {
    const token = window.localStorage.getItem("access_token");
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    body,
    cache: "no-store",
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await safeReadText(response);
  const payload = tryParseJson(text);

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    if (isRecord(payload)) {
      const payloadRecord = payload as Record<string, unknown>;
      if ("detail" in payloadRecord) message = String(payloadRecord.detail);
      else if ("error" in payloadRecord) {
        const err = payloadRecord.error;
        if (isRecord(err) && "message" in err) message = String(err.message);
      }
    }

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}
