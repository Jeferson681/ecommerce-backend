import { apiFetch } from "@/core/http/apiFetch";
import type { Order } from "@/modules/order/types/order";
import type { CheckoutRequest } from "@/modules/payment/types/payment";

export const orderService = {
  list(): Promise<Order[]> {
    return apiFetch<Order[]>("/orders");
  },

  get(id: number): Promise<Order> {
    return apiFetch<Order>(`/orders/${id}`);
  },

  checkout(
    idempotencyKey?: string,
    paymentMethodId?: string
  ): Promise<Order> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers["Idempotency-Key"] = idempotencyKey;
    }

    const body: CheckoutRequest = {
      payment_method_id: paymentMethodId ?? null,
    };

    return apiFetch<Order>("/orders/checkout", {
      method: "POST",
      headers,
      body,
    });
  },
};
