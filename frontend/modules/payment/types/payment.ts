/**
 * Checkout request sent to POST /orders/checkout.
 * Matches PaymentMethodRequest schema in the backend.
 */
export type CheckoutRequest = {
  payment_method_id: string;
};

/**
 * Payment response returned in OrderRead.payments[].
 * Matches PaymentRead schema in the backend.
 */
export type PaymentRead = {
  id: number;
  order_id: number;
  user_id: number;
  amount: string;
  status: string;
  provider: string;
  provider_payment_id: string | null;
  provider_status: string | null;
  provider_reference: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type PaymentStatusType =
  | "pending"
  | "approved"
  | "failed"
  | "cancelled"
  | "refunded";
