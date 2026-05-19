import { apiFetch } from "@/core/http/apiFetch";
import type { LoginRequest, TokenResponse } from "@/modules/auth/types/auth";

export const authService = {
  login(payload: LoginRequest): Promise<TokenResponse> {
    return apiFetch<TokenResponse>("/auth/token", {
      method: "POST",
      body: payload,
    });
  },
};
