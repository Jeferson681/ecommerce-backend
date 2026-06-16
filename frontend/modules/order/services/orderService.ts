import { apiFetch } from "@/core/http/apiFetch";
import type { Order } from "@/modules/order/types/order";

export const orderService = {
  list(): Promise<Order[]> {
    return apiFetch<Order[]>("/orders");
  },

  get(id: number): Promise<Order> {
    return apiFetch<Order>(`/orders/${id}`);
  },

  checkout(
    paymentMethodId: string,
    idempotencyKey?: string
  ): Promise<Order> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers["Idempotency-Key"] = idempotencyKey;
    }

    return apiFetch<Order>("/orders/checkout", {
      method: "POST",
      headers,
      body: { payment_method_id: paymentMethodId },
    });
  },

  retryPayment(
    orderId: number,
    paymentMethodId: string,
    idempotencyKey?: string
  ): Promise<Order> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers["Idempotency-Key"] = idempotencyKey;
    }

    return apiFetch<Order>(`/orders/${orderId}/retry-payment`, {
      method: "POST",
      headers,
      body: { payment_method_id: paymentMethodId },
    });
  },
};
