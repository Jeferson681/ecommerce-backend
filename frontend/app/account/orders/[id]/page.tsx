"use client";

import { useEffect, use, useState, useCallback } from "react";
import Link from "next/link";
import { Loader2, AlertCircle, CreditCard } from "lucide-react";

import { orderService } from "@/modules/order/services/orderService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";
import { productService } from "@/modules/product/services/productService";
import { createIdempotencyKey } from "@/core/utils/idempotency";
import { StripeProvider } from "@/modules/payment/components/StripeProvider";
import { PaymentForm } from "@/modules/payment/components/PaymentForm";
import type { Order } from "@/modules/order/types/order";
import type { Product } from "@/modules/product/types/product";
import type { PaymentRead } from "@/modules/payment/types/payment";
import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

function formatPrice(value: string) {
  const numberValue = Number(value);
  if (Number.isFinite(numberValue)) {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(numberValue);
  }
  return value;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString();
}

const paymentBadge: Record<string, { label: string; classes: string }> = {
  approved: { label: "Approved", classes: "bg-emerald-100 text-emerald-800" },
  pending: { label: "Pending", classes: "bg-amber-100 text-amber-800" },
  failed: { label: "Failed", classes: "bg-red-100 text-red-800" },
  cancelled: { label: "Cancelled", classes: "bg-zinc-100 text-zinc-800" },
  refunded: { label: "Refunded", classes: "bg-blue-100 text-blue-800" },
};

const orderBadge: Record<string, { label: string; classes: string }> = {
  paid: { label: "Paid", classes: "bg-emerald-100 text-emerald-800" },
  pending: { label: "Pending", classes: "bg-amber-100 text-amber-800" },
  cancelled: { label: "Cancelled", classes: "bg-red-100 text-red-800" },
  refunded: { label: "Refunded", classes: "bg-blue-100 text-blue-800" },
};

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [order, setOrder] = useState<Order | null>(null);
  const [productMap, setProductMap] = useState<Map<number, Product>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);

  const loadOrder = useCallback(async () => {
    try {
      const orderData = await orderService.get(Number(resolvedParams.id));
      setOrder(orderData);

      // Resolve product names for order items
      const productIds = orderData.items.map((item) => item.product_id);
      const allProducts = await productService.list();
      const productIndex = new Map(allProducts.map((p) => [p.id, p]));

      for (const pid of productIds) {
        if (productIndex.has(pid)) continue;
        try {
          const product = await productService.get(pid);
          productIndex.set(product.id, product);
        } catch {
          // Skip if product not found
        }
      }
      setProductMap(productIndex);
    } catch (err) {
      setError(getUserErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [resolvedParams.id]);

  useEffect(() => {
    // Defer the initial fetch to a microtask so setState never runs
    // synchronously inside the effect body (react-hooks/set-state-in-effect).
    void Promise.resolve().then(loadOrder);
  }, [loadOrder]);

  async function handleRetryPayment(paymentMethodId: string) {
    setRetrying(true);
    setRetryError(null);

    try {
      const idempotencyKey = createIdempotencyKey();
      const updatedOrder = await orderService.retryPayment(
        Number(resolvedParams.id),
        paymentMethodId,
        idempotencyKey
      );
      setOrder(updatedOrder);
    } catch (err) {
      setRetryError(getUserErrorMessage(err));
    } finally {
      setRetrying(false);
    }
  }

  function canRetry(payment: PaymentRead): boolean {
    return payment.status === "failed";
  }

  if (loading) return <div className="text-sm text-zinc-600">Loading...</div>;
  if (error) return <div className="rounded-sm border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>;
  if (!order) return <div className="text-sm text-zinc-600">Order not found.</div>;

  const lastPayment = order.payments?.[order.payments.length - 1];
  const retryAllowed = lastPayment ? canRetry(lastPayment) : false;
  const ob = orderBadge[order.status] ?? { label: order.status, classes: "bg-zinc-100 text-zinc-800" };

  return (
    <div className="space-y-6">
      <PageHeader title={`Order #${order.id}`} description={`Details for order #${order.id}`} />

      {/* Order info */}
      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-sm text-zinc-600">Created: {formatDate(order.created_at)}</div>
            <span className="text-zinc-300">|</span>
            <div className="text-sm flex items-center gap-2">
              <span className="text-zinc-600">Status:</span>
              <span className={`inline-block rounded-sm px-2 py-0.5 text-xs font-medium ${ob.classes}`}>
                {ob.label}
              </span>
            </div>
          </div>
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

      {/* Payment section */}
      {lastPayment && (
        <Card>
          <CardContent className="space-y-4 p-4">
            <h2 className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500 flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Payment
            </h2>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="text-zinc-600">Status</div>
              <div>
                <span className={`inline-block rounded-sm px-2 py-0.5 text-xs font-medium ${
                  paymentBadge[lastPayment.status]?.classes ?? "bg-zinc-100 text-zinc-800"
                }`}>
                  {paymentBadge[lastPayment.status]?.label ?? lastPayment.status}
                </span>
              </div>

              <div className="text-zinc-600">Provider</div>
              <div className="capitalize">{lastPayment.provider}</div>

              <div className="text-zinc-600">Amount</div>
              <div>{formatPrice(lastPayment.amount)}</div>

              {lastPayment.provider_payment_id && (
                <>
                  <div className="text-zinc-600">Transaction ID</div>
                  <div className="font-mono text-xs break-all">{lastPayment.provider_payment_id}</div>
                </>
              )}

              {lastPayment.provider_status && (
                <>
                  <div className="text-zinc-600">Provider status</div>
                  <div>{lastPayment.provider_status}</div>
                </>
              )}

              {lastPayment.failure_reason && (
                <>
                  <div className="text-zinc-600">Message</div>
                  <div className="text-red-600">{lastPayment.failure_reason}</div>
                </>
              )}

              <div className="text-zinc-600">Last updated</div>
              <div>{formatDate(lastPayment.updated_at)}</div>
            </div>

            {/* Retry section */}
            {retryAllowed && !retrying && (
              <div className="border-t border-zinc-200 pt-4 space-y-4">
                <div className="flex items-center gap-2 text-sm text-zinc-700">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  Payment failed. You can retry with a different payment method.
                </div>

                <StripeProvider>
                  <PaymentForm
                    onPaymentMethodReady={handleRetryPayment}
                    disabled={retrying}
                  />
                </StripeProvider>
              </div>
            )}

            {retrying && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
              </div>
            )}

            {retryError && (
              <div className="rounded-sm border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                {retryError}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button asChild variant="outline" className="rounded-sm">
          <Link href="/account/orders">Back to orders</Link>
        </Button>
        <Button asChild variant="outline" className="rounded-sm">
          <Link href="/products">Continue shopping</Link>
        </Button>
      </div>
    </div>
  );
}
