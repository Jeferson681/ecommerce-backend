"use client";

import { useEffect, use, useState } from "react";

import { orderService } from "@/modules/order/services/orderService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";
import { productService } from "@/modules/product/services/productService";
import type { Order } from "@/modules/order/types/order";
import type { Product } from "@/modules/product/types/product";
import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";

function formatPrice(value: string) {
  const numberValue = Number(value);
  if (Number.isFinite(numberValue)) {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(numberValue);
  }
  return value;
}

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [order, setOrder] = useState<Order | null>(null);
  const [productMap, setProductMap] = useState<Map<number, Product>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const orderData = await orderService.get(Number(resolvedParams.id));
        if (cancelled) return;

        // Resolve product names for order items
        const productIds = orderData.items.map((item) => item.product_id);
        const allProducts = await productService.list();
        const productIndex = new Map(allProducts.map((p) => [p.id, p]));

        // Fetch any products not in the list
        for (const pid of productIds) {
          if (productIndex.has(pid)) continue;
          try {
            const product = await productService.get(pid);
            productIndex.set(product.id, product);
          } catch {
            // Skip if product not found
          }
        }

        if (!cancelled) {
          setOrder(orderData);
          setProductMap(productIndex);
        }
      } catch (err) {
        if (!cancelled) setError(getUserErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [resolvedParams.id]);

  if (loading) return <div className="text-sm text-zinc-600">Loading...</div>;
  if (error) return <div className="rounded-sm border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>;
  if (!order) return <div className="text-sm text-zinc-600">Order not found.</div>;

  return (
    <div className="space-y-6">
      <PageHeader title={`Order #${order.id}`} description={`Details for order #${order.id}`} />

      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="text-sm text-zinc-600">Created: {new Date(order.created_at).toLocaleString()}</div>
          <div className="text-sm text-zinc-600">Items: {order.items.length}</div>

          <div className="space-y-2">
            {order.items.map((it) => {
              const priceNum = Number(it.price);
              const total = Number.isFinite(priceNum) ? priceNum * it.quantity : 0;
              const product = productMap.get(it.product_id);
              const productName = product?.name ?? `Product #${it.product_id}`;
              return (
                <div key={it.id} className="flex items-center justify-between">
                  <div className="text-sm">
                    {productName} <span className="text-zinc-400">&times;{it.quantity}</span>
                  </div>
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
