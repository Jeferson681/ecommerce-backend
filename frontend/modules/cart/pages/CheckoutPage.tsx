"use client";

import { useState, useSyncExternalStore, useRef } from "react";
import {
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  XCircle,
} from "lucide-react";
import Link from "next/link";

import { useCart } from "@/modules/cart/hooks/useCart";
import { formatMoney } from "@/core/utils/money";
import { orderService } from "@/modules/order/services/orderService";
import { paymentService } from "@/modules/payment/services/paymentService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";
import { createIdempotencyKey } from "@/core/utils/idempotency";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import type { Payment } from "@/modules/payment/types/payment";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

type PaymentState =
  | { phase: "idle" }
  | { phase: "ordering" }
  | { phase: "paying"; orderId: number; idempotencyKey: string }
  | { phase: "success" }
  | { phase: "pending"; payment: Payment }
  | { phase: "failed"; reason: string; canRetry: boolean; orderId?: number; idempotencyKey?: string };

export default function CheckoutPage() {
  const { items, subtotal, isEmpty, clear } = useCart();
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  const [paymentState, setPaymentState] = useState<PaymentState>({
    phase: "idle",
  });
  const [error, setError] = useState<string | null>(null);

  // Idempotency key is generated once per logical attempt and reused on retry.
  const idempotencyKeyRef = useRef<string | null>(null);

  if (!hasToken) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Checkout"
          description="Sign in to complete your purchase"
        />
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-700">
              Please sign in to continue with your checkout.
            </p>
            <div className="flex items-center gap-2">
              <Button asChild>
                <Link href="/login?next=/checkout">Sign in</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/signup">Create an account</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="space-y-4">
        <PageHeader title="Checkout" />
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">
              Your cart is empty. Add items before checking out.
            </p>
            <Button asChild>
              <Link href="/products">Browse products</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  async function handlePlaceOrder() {
    setError(null);

    // Generate idempotency key once per logical attempt.
    if (!idempotencyKeyRef.current) {
      idempotencyKeyRef.current = createIdempotencyKey();
    }
    const idempotencyKey = idempotencyKeyRef.current;

    setPaymentState({ phase: "ordering" });

    let orderId: number;

    try {
      const order = await orderService.checkout(idempotencyKey);
      orderId = order.id;
    } catch (err) {
      idempotencyKeyRef.current = null;
      setPaymentState({ phase: "idle" });
      setError(getUserErrorMessage(err));
      return;
    }

    // Order created — now process payment.
    setPaymentState({ phase: "paying", orderId, idempotencyKey });

    try {
      const payment = await paymentService.processPayment(
        { order_id: orderId },
        idempotencyKey
      );

      // Map backend payment status to UX state.
      if (payment.status === "approved") {
        clear();
        setPaymentState({ phase: "success" });
      } else if (payment.status === "pending") {
        clear();
        setPaymentState({ phase: "pending", payment });
      } else {
        // failed, cancelled, refunded — show as failure.
        idempotencyKeyRef.current = null;
        const failureReason = mapPaymentFailure(payment);
        setPaymentState({
          phase: "failed",
          reason: failureReason,
          canRetry: false,
          orderId,
        });
      }
    } catch (err) {
      const message = getUserErrorMessage(err);
      const isTransient = isTransientError(err);

      if (isTransient) {
        // Transient error — can retry with same idempotency key.
        setPaymentState({
          phase: "failed",
          reason: "Connection issue. Please try again.",
          canRetry: true,
          orderId,
          idempotencyKey,
        });
      } else {
        // Non-transient — clear key, show final error.
        idempotencyKeyRef.current = null;
        setPaymentState({
          phase: "failed",
          reason: message,
          canRetry: false,
          orderId,
        });
      }
    }
  }

  async function handleRetry() {
    if (paymentState.phase !== "failed" || !paymentState.canRetry) return;

    const { orderId, idempotencyKey } = paymentState;

    // Keep same idempotency key for retry.
    setPaymentState({ phase: "paying", orderId: orderId!, idempotencyKey: idempotencyKey! });

    try {
      const payment = await paymentService.processPayment(
        { order_id: orderId! },
        idempotencyKey!
      );

      if (payment.status === "approved") {
        clear();
        setPaymentState({ phase: "success" });
      } else if (payment.status === "pending") {
        clear();
        setPaymentState({ phase: "pending", payment });
      } else {
        idempotencyKeyRef.current = null;
        setPaymentState({
          phase: "failed",
          reason: mapPaymentFailure(payment),
          canRetry: false,
          orderId,
        });
      }
    } catch (err) {
      const isTransient = isTransientError(err);
      if (isTransient) {
        setPaymentState({
          phase: "failed",
          reason: "Connection issue. Please try again.",
          canRetry: true,
          orderId,
          idempotencyKey,
        });
      } else {
        idempotencyKeyRef.current = null;
        setPaymentState({
          phase: "failed",
          reason: getUserErrorMessage(err),
          canRetry: false,
          orderId,
        });
      }
    }
  }

  const isProcessing =
    paymentState.phase === "ordering" || paymentState.phase === "paying";

  if (paymentState.phase === "success") {
    return <SuccessConfirmation />;
  }

  if (paymentState.phase === "pending") {
    return <PendingConfirmation payment={paymentState.payment} />;
  }

  if (paymentState.phase === "failed") {
    return (
      <FailureConfirmation
        reason={paymentState.reason}
        canRetry={paymentState.canRetry}
        onRetry={handleRetry}
        isProcessing={isProcessing}
      />
    );
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Checkout" />

      {isEmpty ? (
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">
              Your cart is empty. Add items before checking out.
            </p>
            <Button asChild>
              <Link href="/products">Browse products</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardContent className="p-6">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handlePlaceOrder();
                }}
                className="space-y-4"
              >
                {error && (
                  <div className="rounded-sm border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <div className="rounded-sm border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-600">
                  <p className="mb-1 font-medium text-zinc-800">
                    Order summary
                  </p>
                  <p>
                    You are about to place an order for {items.length} item
                    {items.length !== 1 ? "s" : ""}.
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full rounded-sm bg-[#ffd814] text-sm font-medium text-[#111] hover:bg-[#f7ca00] border-0"
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    "Place your order"
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="h-fit border-zinc-200 bg-white shadow-sm">
            <CardContent className="space-y-3 p-6">
              <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">
                Order Summary
              </div>
              {items.map((item) => (
                <div
                  key={item.product.id}
                  className="flex items-center justify-between text-sm text-zinc-600"
                >
                  <span className="mr-2 truncate">
                    {item.product.name} &times; {item.quantity}
                  </span>
                  <span className="shrink-0">
                    {formatMoney(
                      Number(item.product.price) * item.quantity
                    )}
                  </span>
                </div>
              ))}
              <div className="flex items-center justify-between border-t border-zinc-200 pt-3 text-sm text-zinc-600">
                <span>Shipping</span>
                <span className="font-medium text-green-700">FREE</span>
              </div>
              <div className="flex items-center justify-between border-t border-zinc-200 pt-3 text-base font-semibold">
                <span>Total</span>
                <span>{formatMoney(subtotal)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// --- Sub-components for payment states ---

function SuccessConfirmation() {
  return (
    <div className="space-y-4">
      <PageHeader title="Order confirmed" description="Payment successful" />
      <Card className="border-emerald-200 bg-emerald-50">
        <CardContent className="space-y-4 p-6">
          <CheckCircle2 className="h-10 w-10 text-emerald-600" />
          <div>
            <div className="text-lg font-semibold text-emerald-950">
              Thank you for your order
            </div>
            <p className="mt-1 text-sm text-emerald-800">
              Your payment has been approved and your order is being processed.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button asChild className="rounded-sm">
              <Link href="/account/orders">View your orders</Link>
            </Button>
            <Button asChild variant="outline" className="rounded-sm">
              <Link href="/products">Continue shopping</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PendingConfirmation({ payment }: { payment: Payment }) {
  return (
    <div className="space-y-4">
      <PageHeader
        title="Payment pending"
        description="Awaiting confirmation"
      />
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="space-y-4 p-6">
          <Clock className="h-10 w-10 text-amber-600" />
          <div>
            <div className="text-lg font-semibold text-amber-950">
              Your payment is pending confirmation
            </div>
            <p className="mt-1 text-sm text-amber-800">
              We received your order but the payment is still being confirmed.
              This usually takes a few moments.
            </p>
            <p className="mt-2 text-sm text-amber-700">
              Order #{payment.order_id} &middot;{" "}
              {formatMoney(Number(payment.amount))}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button asChild className="rounded-sm">
              <Link href="/account/orders">View order status</Link>
            </Button>
            <Button asChild variant="outline" className="rounded-sm">
              <Link href="/products">Continue shopping</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function FailureConfirmation({
  reason,
  canRetry,
  onRetry,
  isProcessing,
}: {
  reason: string;
  canRetry: boolean;
  onRetry: () => void;
  isProcessing: boolean;
}) {
  return (
    <div className="space-y-4">
      <PageHeader title="Payment failed" description="Unable to process payment" />
      <Card className="border-red-200 bg-red-50">
        <CardContent className="space-y-4 p-6">
          {canRetry ? (
            <AlertCircle className="h-10 w-10 text-amber-600" />
          ) : (
            <XCircle className="h-10 w-10 text-red-600" />
          )}
          <div>
            <div className="text-lg font-semibold text-red-950">
              Payment could not be processed
            </div>
            <p className="mt-1 text-sm text-red-800">{reason}</p>
          </div>
          <div className="flex items-center gap-2">
            {canRetry && (
              <Button
                onClick={onRetry}
                className="rounded-sm"
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  "Try again"
                )}
              </Button>
            )}
            <Button asChild variant="outline" className="rounded-sm">
              <Link href="/cart">Return to cart</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// --- Helpers ---

function mapPaymentFailure(payment: Payment): string {
  if (payment.failure_reason) {
    return "Payment could not be processed.";
  }
  return "Payment could not be processed.";
}

function isTransientError(err: unknown): boolean {
  if (err instanceof TypeError && err.message === "Failed to fetch") {
    return true;
  }
  if (err && typeof err === "object" && "status" in err) {
    const status = (err as { status: number }).status;
    // 408 Request Timeout, 429 Too Many Requests, 5xx Server errors are transient.
    if (status === 408 || status === 429) return true;
    if (status >= 500 && status < 600) return true;
    // 0 means network error (no response).
    if (status === 0) return true;
  }
  return false;
}
