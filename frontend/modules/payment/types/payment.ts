/** Payment types matching backend PaymentRead schema. */

export type PaymentStatus = "pending" | "approved" | "failed" | "cancelled" | "refunded";

export type Payment = {
  id: number;
  order_id: number;
  user_id: number;
  amount: string;
  status: PaymentStatus;
  provider: string;
  provider_payment_id: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type PaymentCreate = {
  order_id: number;
};
