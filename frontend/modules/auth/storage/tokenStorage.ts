const ACCESS_TOKEN_KEY = "access_token";
const TOKEN_EVENT = "auth_token_changed";

type Listener = () => void;

function notify(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(TOKEN_EVENT));
}

export const tokenStorage = {
  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
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
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
    notify();
  },

  clear(): void {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    notify();
  },
};
