import { ApiError } from "@/core/exceptions/ApiError";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function extractBackendError(payload: unknown): { type?: string; message?: string } {
  if (!isRecord(payload)) return {};

  const detail = typeof payload.detail === "string" ? payload.detail : undefined;
  if (detail) return { message: detail };

  const error = payload.error;
  if (!isRecord(error)) return {};

  return {
    type: typeof error.type === "string" ? error.type : undefined,
    message: typeof error.message === "string" ? error.message : undefined,
  };
}

function mapStatusToMessage(status: number): string {
  if (status === 400 || status === 422) {
    return "We couldn't process your request. Please check your information and try again.";
  }
  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }
  if (status === 403) {
    return "You don't have permission to perform this action.";
  }
  if (status === 404) {
    return "We couldn't find what you were looking for.";
  }
  if (status === 409) {
    return "This action couldn't be completed due to a conflict. Please refresh and try again.";
  }
  if (status === 429) {
    return "Too many requests. Please wait a moment and try again.";
  }
  if (status >= 500) {
    return "Something went wrong on our side. Please try again in a few minutes.";
  }
  return "Something went wrong. Please try again.";
}

function mapBackendMessage(message?: string): string | null {
  if (!message) return null;

  const normalized = message.trim().toLowerCase();

  // Check for prefix matches (messages that may have suffixed details like "(product_id=5)")
  if (normalized.startsWith("insufficient stock for product")) {
    return "One or more items are out of stock. Update your cart and try again.";
  }

  const knownMessages: Record<string, string> = {
    "email already exists.": "This email is already in use. Try signing in or use another email.",
    "invalid email or password.": "Invalid email or password.",
    "user not found.": "We couldn't find that user.",
    "product not found.": "We couldn't find that product.",
    "cart not found.": "We couldn't find your cart.",
    "cart item not found.": "We couldn't find that cart item.",
    "order not found.": "We couldn't find that order.",
    "cart is empty. add items before checkout.": "Your cart is empty. Add items before checkout.",
    "credential does not meet the required policy.":
      "Your password doesn't meet security requirements. Use at least 8 characters with uppercase, lowercase, number, and symbol.",
    "an internal server error occurred.": "Something went wrong on our side. Please try again in a few minutes.",
  };

  return knownMessages[normalized] ?? null;
}

function mapBackendType(type?: string): string | null {
  if (!type) return null;

  const knownTypes: Record<string, string> = {
    AuthenticationError: "Your session has expired. Please sign in again.",
    AuthorizationError: "You don't have permission to perform this action.",
    NotFoundError: "We couldn't find what you were looking for.",
    ValidationError: "Some fields are invalid. Please review and try again.",
    InternalServerError: "Something went wrong on our side. Please try again in a few minutes.",
  };

  return knownTypes[type] ?? null;
}

export function buildFriendlyApiMessage(status: number, payload: unknown): string {
  const backend = extractBackendError(payload);

  const mappedByMessage = mapBackendMessage(backend.message);
  if (mappedByMessage) return mappedByMessage;

  const mappedByType = mapBackendType(backend.type);
  if (mappedByType) return mappedByType;

  return mapStatusToMessage(status);
}

export function getUserErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status <= 0) {
      return "Unable to connect to the server. Please check your connection and try again.";
    }
    return buildFriendlyApiMessage(error.status, error.details);
  }

  if (error instanceof Error) {
    return "Something unexpected happened. Please try again.";
  }

  return "Something went wrong. Please try again.";
}
