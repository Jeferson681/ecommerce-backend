"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { orderService } from "@/modules/order/services/orderService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";
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

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function SkeletonRow() {
  return (
    <Card className="animate-pulse">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-4 w-24 rounded bg-zinc-200" />
            <div className="h-3 w-16 rounded bg-zinc-200" />
          </div>
          <div className="h-4 w-20 rounded bg-zinc-200" />
        </div>
      </CardContent>
    </Card>
  );
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
        if (!cancelled) setError(getUserErrorMessage(err));
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
      <PageHeader title="My orders" description={loading ? "" : `${orders.length} order${orders.length !== 1 ? "s" : ""}`} />

      {loading ? (
        <div className="grid grid-cols-1 gap-4">
          {[1, 2, 3].map((i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      ) : error ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4 text-sm text-amber-800">{error}</CardContent>
        </Card>
      ) : orders.length === 0 ? (
        <Card>
          <CardContent className="p-6 space-y-3">
            <p className="text-sm text-zinc-600">You have no orders yet.</p>
            <Link href="/products" className="text-sm font-medium text-[#007185] hover:text-[#c7511f] hover:underline">
              Browse products
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {orders.map((o) => {
            const total = o.items.reduce(
              (sum, it) => sum + (Number.isFinite(Number(it.price)) ? Number(it.price) * it.quantity : 0),
              0
            );
            return (
              <Card key={o.id} className="hover:shadow-sm transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold leading-tight">
                        <Link href={`/account/orders/${o.id}`} className="underline-offset-4 hover:underline">
                          Order #{o.id}
                        </Link>
                      </h3>
                      <div className="mt-1 text-xs text-zinc-500">
                        {o.items.length} item{o.items.length !== 1 ? "s" : ""} &middot; {formatDate(o.created_at)}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`inline-block rounded-sm px-2 py-0.5 text-xs font-medium ${
                        o.status === "paid" ? "bg-emerald-100 text-emerald-800" :
                        o.status === "pending" ? "bg-amber-100 text-amber-800" :
                        o.status === "cancelled" ? "bg-red-100 text-red-800" :
                        o.status === "refunded" ? "bg-blue-100 text-blue-800" :
                        "bg-zinc-100 text-zinc-800"
                      }`}>
                        {o.status}
                      </span>
                      <div className="text-sm font-medium text-zinc-900 whitespace-nowrap">
                        {formatPrice(total.toString())}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
