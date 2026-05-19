"use client";

import Link from "next/link";
import { Minus, Plus, Trash2 } from "lucide-react";

import { useCart } from "@/modules/cart/hooks/useCart";
import { formatMoney } from "@/core/utils/money";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

export default function CartPage() {
  const { items, subtotal, isEmpty, updateQuantity, removeItem } = useCart();

  return (
    <div className="space-y-6">
      <PageHeader title="Your cart" description="Manage items before checkout" />

      {isEmpty ? (
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm text-zinc-600">Your cart is empty.</p>
            <Button asChild>
              <Link href="/products">Go shopping</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card>
            <CardContent className="space-y-4 p-4 sm:p-6">
              {items.map((item) => (
                <div key={item.product.id} className="flex flex-col gap-4 rounded-2xl border border-zinc-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <Link href={`/products/${item.product.id}`} className="text-sm font-semibold hover:underline">
                      {item.product.name}
                    </Link>
                    <div className="text-sm text-zinc-600">{formatMoney(item.product.price)} each</div>
                    <div className="text-xs text-zinc-500">Stock {item.product.stock_quantity}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="icon" onClick={() => updateQuantity(item.product.id, item.quantity - 1)}>
                      <Minus className="h-4 w-4" />
                    </Button>
                    <div className="w-10 text-center text-sm font-medium">{item.quantity}</div>
                    <Button variant="outline" size="icon" onClick={() => updateQuantity(item.product.id, item.quantity + 1)}>
                      <Plus className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => removeItem(item.product.id)}>
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="h-fit border-zinc-200 bg-white shadow-sm">
            <CardContent className="space-y-4 p-6">
              <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Summary</div>
              <div className="flex items-center justify-between text-sm text-zinc-600">
                <span>Subtotal</span>
                <span>{formatMoney(subtotal)}</span>
              </div>
              <div className="flex items-center justify-between text-sm text-zinc-600">
                <span>Shipping</span>
                <span>Calculated at checkout</span>
              </div>
              <div className="flex items-center justify-between border-t border-zinc-200 pt-4 text-base font-semibold">
                <span>Total</span>
                <span>{formatMoney(subtotal)}</span>
              </div>
              <Button asChild className="w-full rounded-full">
                <Link href="/checkout">Proceed to checkout</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
