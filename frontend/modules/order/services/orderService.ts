import { apiFetch } from "@/core/http/apiFetch";
import type { Order } from "@/modules/order/types/order";

export const orderService = {
  list(): Promise<Order[]> {
    return apiFetch<Order[]>("/orders");
  },

  get(id: number): Promise<Order> {
    return apiFetch<Order>(`/orders/${id}`);
  },
};
