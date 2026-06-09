/**
 * Payment method types supported by the backend.
 * Matches PaymentMethod Literal in payment/gateway/base.py.
 */
export type PaymentMethod = "card" | "pix" | "boleto";

/**
 * Checkout request sent to POST /orders/checkout.
 * Matches CheckoutRequest schema in the backend.
 */
export type CheckoutRequest = {
  payment_method_id?: string | null;
};
