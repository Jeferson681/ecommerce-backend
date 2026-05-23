"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { orderService } from "@/modules/order/services/orderService";
import type { Order } from "@/modules/order/types/order";
import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";

function formatPrice(value: string) {
  const numberValue = Number(value);
  if (Number.isFinite(numberValue)) {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(numberValue);
  }
  return value;
}

export default function Page() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    orderService
      .list()
      .then((data) => {
        if (!cancelled) setOrders(data || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader title="My orders" description="List of your orders" />

      {loading ? (
        <div className="text-sm text-zinc-600">Loading...</div>
      ) : error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>
      ) : orders.length === 0 ? (
        <div className="text-sm text-zinc-600">You have no orders yet.</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {orders.map((o) => (
            <Card key={o.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold leading-tight">
                      <Link href={`/account/orders/${o.id}`} className="underline-offset-4 hover:underline">
                        Order #{o.id}
                      </Link>
                    </h3>
                    <div className="text-xs text-zinc-500">Items: {o.items.length}</div>
                  </div>
                  <div className="text-sm font-medium text-zinc-900 whitespace-nowrap">{formatPrice(o.items.reduce((s, it) => s + (Number.isFinite(Number(it.price)) ? Number(it.price) * it.quantity : 0), 0).toString())}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
