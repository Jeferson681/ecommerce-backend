import { apiFetch } from "@/core/http/apiFetch";
import type { LoginRequest, TokenResponse } from "@/modules/auth/types/auth";

export const authService = {
  login(payload: LoginRequest): Promise<TokenResponse> {
    return apiFetch<TokenResponse>("/auth/token", {
      method: "POST",
      body: payload,
    });
  },

  logout(refreshToken: string): Promise<void> {
    return apiFetch<void>("/auth/logout", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });
  },

  refresh(refreshToken: string): Promise<TokenResponse> {
    return apiFetch<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });
  },
};
