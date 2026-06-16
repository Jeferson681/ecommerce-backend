"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";
import { adminOrderService } from "@/modules/order/services/adminOrderService";
import { formatMoney } from "@/core/utils/money";
import type { Order } from "@/modules/order/types/order";

export default function Page() {
  const adminEnabled = process.env.NEXT_PUBLIC_ENABLE_ADMIN === "true";
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!adminEnabled) return;
    adminOrderService
      .listAll()
      .then(setOrders)
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, [adminEnabled]);

  if (!adminEnabled) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Admin" description="Backoffice (MVP stub)" />
      <Card>
        <CardContent className="p-6 space-y-2">
          <p className="text-sm text-zinc-700">Admin area is intentionally minimal for now.</p>
          <div className="text-sm">
            <Link href="/users" className="underline underline-offset-4">
              Manage users
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Orders</h2>
          {loading ? (
            <p className="text-sm text-zinc-500">Loading orders...</p>
          ) : orders.length === 0 ? (
            <p className="text-sm text-zinc-500">No orders found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-zinc-500">
                    <th className="pb-2 pr-4">ID</th>
                    <th className="pb-2 pr-4">User</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Items</th>
                    <th className="pb-2 pr-4">Total</th>
                    <th className="pb-2">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => {
                    const total = order.items.reduce(
                      (sum, item) => sum + Number(item.price) * item.quantity,
                      0
                    );
                    return (
                      <tr key={order.id} className="border-b last:border-0">
                        <td className="py-2 pr-4">#{order.id}</td>
                        <td className="py-2 pr-4">{order.user_id}</td>
                        <td className="py-2 pr-4">
                          <span className={`inline-block rounded-sm px-2 py-0.5 text-xs font-medium ${
                            order.status === "paid" ? "bg-emerald-100 text-emerald-800" :
                            order.status === "pending" ? "bg-amber-100 text-amber-800" :
                            order.status === "cancelled" ? "bg-red-100 text-red-800" :
                            order.status === "refunded" ? "bg-blue-100 text-blue-800" :
                            "bg-zinc-100 text-zinc-800"
                          }`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4">{order.items.length}</td>
                        <td className="py-2 pr-4">{formatMoney(total)}</td>
                        <td className="py-2">
                          {new Date(order.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
