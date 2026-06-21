"use client";

import { useState, useSyncExternalStore, useRef } from "react";
import { useRouter } from "next/navigation";
import { Loader2, AlertCircle, XCircle } from "lucide-react";
import Link from "next/link";

import { useCart } from "@/modules/cart/hooks/useCart";
import { cartStorage } from "@/modules/cart/storage/cartStorage";
import { formatMoney } from "@/core/utils/money";
import { orderService } from "@/modules/order/services/orderService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";
import { createIdempotencyKey } from "@/core/utils/idempotency";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { StripeProvider } from "@/modules/payment/components/StripeProvider";
import { PaymentForm } from "@/modules/payment/components/PaymentForm";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

type CheckoutState =
  | { phase: "idle" }
  | { phase: "ordering" }
  | { phase: "failed"; reason: string; canRetry: boolean };

export default function CheckoutPage() {
  const router = useRouter();
  const { items, subtotal, isEmpty, clear } = useCart();
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  const [checkoutState, setCheckoutState] = useState<CheckoutState>({
    phase: "idle",
  });

  const paymentMethodIdRef = useRef<string | null>(null);
  const idempotencyKeyRef = useRef<string | null>(null);

  const isProcessing = checkoutState.phase === "ordering";

  if (!hasToken) {
    return (
      <div className="space-y-4">
        <PageHeader title="Checkout" description="Sign in to complete your purchase" />
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-700">Please sign in to continue with your checkout.</p>
            <div className="flex items-center gap-2">
              <Button asChild><Link href="/login?next=/checkout">Sign in</Link></Button>
              <Button asChild variant="outline"><Link href="/signup">Create an account</Link></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (checkoutState.phase === "failed") {
    return (
      <FailureConfirmation
        reason={checkoutState.reason}
        canRetry={checkoutState.canRetry}
        onRetry={handleRetry}
        isProcessing={isProcessing}
      />
    );
  }

  if (isEmpty) {
    return (
      <div className="space-y-4">
        <PageHeader title="Checkout" />
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">Your cart is empty. Add items before checking out.</p>
            <Button asChild><Link href="/products">Browse products</Link></Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  function handlePaymentMethodReady(paymentMethodId: string) {
    paymentMethodIdRef.current = paymentMethodId;
    if (!idempotencyKeyRef.current) {
      idempotencyKeyRef.current = createIdempotencyKey();
    }
    placeOrder();
  }

  async function placeOrder() {
    const idempotencyKey = idempotencyKeyRef.current;
    const paymentMethodId = paymentMethodIdRef.current;

    setCheckoutState({ phase: "ordering" });

    try {
      await cartStorage.syncLocalBeforeCheckout();

      const order = await orderService.checkout(paymentMethodId!, idempotencyKey ?? undefined);

      clear();

      // Redirect to dedicated status page — no inline success state
      router.push(`/orders/${order.id}/status`);
    } catch (err) {
      const message = getUserErrorMessage(err);
      const isTransient = isTransientError(err);

      if (isTransient) {
        setCheckoutState({ phase: "failed", reason: "Connection issue. Please try again.", canRetry: true });
      } else {
        idempotencyKeyRef.current = null;
        paymentMethodIdRef.current = null;
        setCheckoutState({ phase: "failed", reason: message, canRetry: false });
      }
    }
  }

  async function handleRetry() {
    if (checkoutState.phase !== "failed" || !checkoutState.canRetry) return;

    const idempotencyKey = idempotencyKeyRef.current;
    const paymentMethodId = paymentMethodIdRef.current;
    if (!idempotencyKey) return;

    setCheckoutState({ phase: "ordering" });

    try {
      await cartStorage.syncLocalBeforeCheckout();

      const order = await orderService.checkout(paymentMethodId!, idempotencyKey);

      clear();
      router.push(`/orders/${order.id}/status`);
    } catch (err) {
      const isTransient = isTransientError(err);
      if (isTransient) {
        setCheckoutState({ phase: "failed", reason: "Connection issue. Please try again.", canRetry: true });
      } else {
        idempotencyKeyRef.current = null;
        paymentMethodIdRef.current = null;
        setCheckoutState({ phase: "failed", reason: getUserErrorMessage(err), canRetry: false });
      }
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Checkout" />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardContent className="p-6 space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Payment method</h2>

            {checkoutState.phase === "idle" ? (
              <StripeProvider>
                <PaymentForm onPaymentMethodReady={handlePaymentMethodReady} disabled={isProcessing} />
              </StripeProvider>
            ) : (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="h-fit border-zinc-200 bg-white shadow-sm">
          <CardContent className="space-y-3 p-6">
            <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Order Summary</div>
            {items.map((item) => (
              <div key={item.product.id} className="flex items-center justify-between text-sm text-zinc-600">
                <span className="mr-2 truncate">{item.product.name} &times; {item.quantity}</span>
                <span className="shrink-0">{formatMoney(Number(item.product.price) * item.quantity)}</span>
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
      <PageHeader title="Checkout failed" description="Unable to complete checkout" />
      <Card className="border-red-200 bg-red-50">
        <CardContent className="space-y-4 p-6">
          {canRetry ? <AlertCircle className="h-10 w-10 text-amber-600" /> : <XCircle className="h-10 w-10 text-red-600" />}
          <div>
            <div className="text-lg font-semibold text-red-950">Checkout could not be completed</div>
            <p className="mt-1 text-sm text-red-800">{reason}</p>
          </div>
          <div className="flex items-center gap-2">
            {canRetry && (
              <Button onClick={onRetry} className="rounded-sm" disabled={isProcessing}>
                {isProcessing ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Retrying...</>
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

function isTransientError(err: unknown): boolean {
  if (err instanceof TypeError && err.message === "Failed to fetch") return true;
  if (err && typeof err === "object" && "status" in err) {
    const status = (err as { status: number }).status;
    if (status === 408 || status === 429) return true;
    if (status >= 500 && status < 600) return true;
    if (status === 0) return true;
  }
  return false;
}
