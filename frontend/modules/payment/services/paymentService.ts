import { apiFetch } from "@/core/http/apiFetch";
import type { Payment, PaymentCreate } from "@/modules/payment/types/payment";

export const paymentService = {
  processPayment(
    payload: PaymentCreate,
    idempotencyKey?: string
  ): Promise<Payment> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers["Idempotency-Key"] = idempotencyKey;
    }
    return apiFetch<Payment>("/payments", {
      method: "POST",
      body: payload,
      headers,
    });
  },

  getPayment(paymentId: number): Promise<Payment> {
    return apiFetch<Payment>(`/payments/${paymentId}`);
  },
};
