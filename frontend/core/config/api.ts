/**
 * API base URL configuration.
 *
 * Priority:
 * 1. `NEXT_PUBLIC_API_URL` environment variable (for Docker/production)
 * 2. `localhost:8000` fallback (local development)
 */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
