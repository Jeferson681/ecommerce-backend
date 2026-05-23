"use client";

import { useEffect, useState } from "react";

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

export default function Page({ params }: { params: { id: string } }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    orderService
      .get(Number(params.id))
      .then((data) => {
        if (!cancelled) setOrder(data);
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
  }, [params.id]);

  if (loading) return <div className="text-sm text-zinc-600">Loading...</div>;
  if (error) return <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>;
  if (!order) return <div className="text-sm text-zinc-600">Order not found.</div>;

  return (
    <div className="space-y-6">
      <PageHeader title={`Order #${order.id}`} description={`Details for order #${order.id}`} />

      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="text-sm">Created: {new Date(order.created_at).toLocaleString()}</div>
          <div className="text-sm">Items: {order.items.length}</div>
          <div className="space-y-2">
            {order.items.map((it) => {
              const priceNum = Number(it.price);
              const total = Number.isFinite(priceNum) ? priceNum * it.quantity : 0;
              return (
                <div key={it.id} className="flex items-center justify-between">
                  <div className="text-sm">Product {it.product_id} x{it.quantity}</div>
                  <div className="text-sm font-medium">{formatPrice(total.toString())}</div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
