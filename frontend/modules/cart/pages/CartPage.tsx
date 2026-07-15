"use client";

import Link from "next/link";
import { Minus, Plus, Trash2 } from "lucide-react";
import { useSyncExternalStore } from "react";

import { useCart } from "@/modules/cart/hooks/useCart";
import { formatMoney } from "@/core/utils/money";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

export default function CartPage() {
  const { items, subtotal, isEmpty, updateQuantity, removeItem } = useCart();
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  const checkoutHref = hasToken ? "/checkout" : "/login?next=/checkout";
  const checkoutLabel = hasToken ? "Proceed to checkout" : "Sign in to checkout";

  return (
    <div className="space-y-6">
      <PageHeader title="Shopping Cart" description={isEmpty ? "" : `${items.length} item${items.length !== 1 ? "s" : ""}`} />

      {isEmpty ? (
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">Your cart is empty.</p>
            <Button asChild>
              <Link href="/products">Browse products</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card>
            <CardContent className="space-y-4 p-4 sm:p-6">
              {items.map((item) => (
                <div key={item.product.id} className="flex flex-col gap-4 rounded-sm border border-zinc-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex-1 space-y-1">
                    <Link href={`/products/${item.product.id}`} className="text-sm font-semibold hover:underline">
                      {item.product.name}
                    </Link>
                    <div className="text-sm text-zinc-600">{formatMoney(item.product.price)} each</div>
                    <div className="text-xs text-zinc-500">
                      {item.product.stock_quantity > 0 ? "In Stock" : "Out of stock"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                      className="h-8 w-8"
                    >
                      <Minus className="h-3 w-3" />
                    </Button>
                    <div className="w-10 text-center text-sm font-medium">{item.quantity}</div>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                      className="h-8 w-8"
                    >
                      <Plus className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeItem(item.product.id)}
                      className="h-8 w-8 text-zinc-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="h-fit border-zinc-200 bg-white shadow-sm">
            <CardContent className="space-y-4 p-6">
              <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Order Summary</div>
              <div className="flex items-center justify-between text-sm text-zinc-600">
                <span>Subtotal ({items.length} item{items.length !== 1 ? "s" : ""})</span>
                <span className="font-medium text-zinc-900">{formatMoney(subtotal)}</span>
              </div>
              <div className="flex items-center justify-between text-sm text-zinc-600">
                <span>Shipping</span>
                <span className="text-green-700 font-medium">FREE</span>
              </div>
              <div className="flex items-center justify-between border-t border-zinc-200 pt-4 text-base font-semibold">
                <span>Total</span>
                <span>{formatMoney(subtotal)}</span>
              </div>
              <Button asChild className="w-full">
                <Link href={checkoutHref}>{checkoutLabel}</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
