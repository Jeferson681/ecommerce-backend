"use client";

import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import Link from "next/link";

import { useCart } from "@/modules/cart/hooks/useCart";
import { formatMoney } from "@/core/utils/money";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";

export default function CheckoutPage() {
  const { items, subtotal, isEmpty, clear } = useCart();
  const [completed, setCompleted] = useState(false);
  const [orderNumber, setOrderNumber] = useState<string | null>(null);
  const [email, setEmail] = useState("");

  function placeOrder(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCompleted(true);
    setOrderNumber(`ORD-${Math.floor(Math.random() * 900000 + 100000)}`);
    clear();
  }

  if (completed) {
    return (
      <Card className="border-emerald-200 bg-emerald-50">
        <CardContent className="space-y-4 p-6">
          <CheckCircle2 className="h-10 w-10 text-emerald-600" />
          <div>
            <div className="text-lg font-semibold text-emerald-950">Order placed successfully</div>
            <p className="mt-1 text-sm text-emerald-800">
              This is a demo checkout flow. No backend payment was called.
            </p>
          </div>
          <div className="text-sm text-emerald-900">Order number: {orderNumber}</div>
          <Button asChild className="rounded-full">
            <Link href="/products">Continue shopping</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Checkout" description="Demo checkout without backend payment integration" />

      {isEmpty ? (
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">Add items to your cart before checking out.</p>
            <Button asChild>
              <Link href="/products">Go to catalog</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardContent className="p-6">
              <form onSubmit={placeOrder} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label htmlFor="checkout-full-name" className="text-sm font-medium">Full name</label>
                    <Input id="checkout-full-name" required placeholder="Your name" />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="checkout-email" className="text-sm font-medium">Email</label>
                    <Input id="checkout-email" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="checkout-note" className="text-sm font-medium">Delivery note</label>
                  <Input id="checkout-note" placeholder="Optional instructions for delivery" />
                </div>

                <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-600">
                  Payment methods and shipping integrations are intentionally mocked in the frontend only.
                </div>

                <Button type="submit" className="rounded-full px-6">
                  Place order
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="h-fit border-zinc-200 bg-white shadow-sm">
            <CardContent className="space-y-3 p-6">
              <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Order review</div>
              {items.map((item) => (
                <div key={item.product.id} className="flex items-center justify-between text-sm text-zinc-600">
                  <span>{item.product.name} × {item.quantity}</span>
                  <span>{formatMoney(Number(item.product.price) * item.quantity)}</span>
                </div>
              ))}
              <div className="flex items-center justify-between border-t border-zinc-200 pt-4 text-base font-semibold">
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
