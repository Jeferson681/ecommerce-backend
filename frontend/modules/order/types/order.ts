import type { PaymentRead } from "@/modules/payment/types/payment";

export type OrderStatus = "pending" | "paid" | "cancelled" | "refunded";

export type OrderItem = {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  price: string;
  created_at: string;
  updated_at: string;
};

export type Order = {
  id: number;
  user_id: number;
  status: OrderStatus;
  items: OrderItem[];
  payments: PaymentRead[];
  created_at: string;
  updated_at: string;
};
