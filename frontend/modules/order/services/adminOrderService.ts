import { apiFetch } from "@/core/http/apiFetch";
import type { Order } from "@/modules/order/types/order";

export const adminOrderService = {
  listAll(): Promise<Order[]> {
    return apiFetch<Order[]>("/admin/orders");
  },
};
