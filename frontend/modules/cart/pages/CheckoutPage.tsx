"use client";

import { useState, useSyncExternalStore } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useCart } from "@/modules/cart/hooks/useCart";
import { formatMoney } from "@/core/utils/money";
import { orderService } from "@/modules/order/services/orderService";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

export default function CheckoutPage() {
  const router = useRouter();
  const { items, subtotal, isEmpty, clear } = useCart();
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  const [completed, setCompleted] = useState(false);
  const [orderId, setOrderId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!hasToken) {
    return (
      <div className="space-y-4">
        <PageHeader title="Checkout" description="Sign in to complete your purchase" />
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-700">Please sign in to continue with your checkout.</p>
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

  async function placeOrder(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const order = await orderService.checkout();
      setOrderId(order.id);
      setCompleted(true);
      clear();
    } catch (err) {
      setError(getUserErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  if (completed) {
    return (
      <div className="space-y-4">
        <PageHeader title="Order confirmed" description="Your order has been placed" />
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="space-y-4 p-6">
            <CheckCircle2 className="h-10 w-10 text-emerald-600" />
            <div>
              <div className="text-lg font-semibold text-emerald-950">Thank you for your order</div>
              <p className="mt-1 text-sm text-emerald-800">
                Your order #{orderId} has been placed and is being processed.
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

  return (
    <div className="space-y-4">
      <PageHeader title="Checkout" />

      {isEmpty ? (
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">Your cart is empty. Add items before checking out.</p>
            <Button asChild>
              <Link href="/products">Browse products</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardContent className="p-6">
              <form onSubmit={placeOrder} className="space-y-4">
                {error && (
                  <div className="rounded-sm border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <div className="rounded-sm border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-600">
                  <p className="font-medium text-zinc-800 mb-1">Order summary</p>
                  <p>You are about to place an order for {items.length} item{items.length !== 1 ? "s" : ""}.</p>
                </div>

                <Button
                  type="submit"
                  className="w-full rounded-sm bg-[#ffd814] text-sm font-medium text-[#111] hover:bg-[#f7ca00] border-0"
                  disabled={loading}
                >
                  {loading ? (
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
              <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Order Summary</div>
              {items.map((item) => (
                <div key={item.product.id} className="flex items-center justify-between text-sm text-zinc-600">
                  <span className="truncate mr-2">{item.product.name} &times; {item.quantity}</span>
                  <span className="shrink-0">{formatMoney(Number(item.product.price) * item.quantity)}</span>
                </div>
              ))}
              <div className="flex items-center justify-between border-t border-zinc-200 pt-3 text-sm text-zinc-600">
                <span>Shipping</span>
                <span className="text-green-700 font-medium">FREE</span>
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
