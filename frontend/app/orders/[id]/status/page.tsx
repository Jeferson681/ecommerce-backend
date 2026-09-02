"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import Link from "next/link";

import { orderService } from "@/modules/order/services/orderService";
import { formatMoney } from "@/core/utils/money";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

type PaymentStatus = "pending" | "approved" | "failed" | "cancelled" | "refunded";
type PollingPhase = "loading" | "polling" | "done" | "error";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES: PaymentStatus[] = ["approved", "failed", "cancelled", "refunded"];

const paymentStatusConfig: Record<string, { icon: typeof CheckCircle2; color: string; bg: string; label: string; description: string }> = {
  approved: { icon: CheckCircle2, color: "text-emerald-600", bg: "border-emerald-200 bg-emerald-50", label: "Payment approved", description: "Your order is now being processed." },
  pending: { icon: Loader2, color: "text-amber-600", bg: "border-amber-200 bg-amber-50", label: "Processing payment...", description: "Your payment is being processed. This should only take a few seconds." },
  failed: { icon: XCircle, color: "text-red-600", bg: "border-red-200 bg-red-50", label: "Payment failed", description: "The payment was declined. You can try again from your orders." },
  cancelled: { icon: XCircle, color: "text-zinc-600", bg: "border-zinc-200 bg-zinc-50", label: "Payment cancelled", description: "The payment was cancelled." },
  refunded: { icon: CheckCircle2, color: "text-blue-600", bg: "border-blue-200 bg-blue-50", label: "Payment refunded", description: "The payment has been refunded." },
};

export default function OrderStatusPage({ params }: { params: Promise<{ id: string }> }) {
  const [orderId, setOrderId] = useState<number | null>(null);
  const [order, setOrder] = useState<Awaited<ReturnType<typeof orderService.get>> | null>(null);
  const [pollingPhase, setPollingPhase] = useState<PollingPhase>("loading");
  const [error, setError] = useState<string | null>(null);
  const pollingPhaseRef = useRef<PollingPhase>("loading");

  useEffect(() => {
    params.then((p) => {
      const id = Number(p.id);
      if (isNaN(id)) {
        setError("Invalid order ID.");
        setPollingPhase("error");
        return;
      }
      setOrderId(id);
    });
  }, [params]);

  const loadOrder = useCallback(async () => {
    if (!orderId) return;
    try {
      const data = await orderService.get(orderId);
      setOrder(data);

      const lastPayment = data.payments?.[data.payments.length - 1];
      const paymentStatus: PaymentStatus = (lastPayment?.status as PaymentStatus) ?? "pending";

      if (TERMINAL_STATUSES.includes(paymentStatus)) {
        setPollingPhase("done");
        pollingPhaseRef.current = "done";
      } else if (pollingPhaseRef.current === "loading") {
        setPollingPhase("polling");
        pollingPhaseRef.current = "polling";
      }
    } catch {
      setError("Could not load order details.");
      setPollingPhase("error");
      pollingPhaseRef.current = "error";
    }
  }, [orderId]);

  useEffect(() => {
    if (!orderId) return;

    // Defer the initial poll to a microtask so setState never runs
    // synchronously inside the effect body (react-hooks/set-state-in-effect).
    void Promise.resolve().then(loadOrder);

    const interval = setInterval(loadOrder, POLL_INTERVAL_MS);
    const timeout = setTimeout(() => {
      clearInterval(interval);
      if (pollingPhaseRef.current !== "done") {
        setPollingPhase("error");
        pollingPhaseRef.current = "error";
        setError("Payment is taking longer than expected. Check your orders for updates.");
      }
    }, 60_000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [orderId, loadOrder]);

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Order status" description="Error loading order" />
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6 space-y-4">
            <p className="text-sm text-red-800">{error}</p>
            <div className="flex gap-2">
              <Button asChild variant="outline"><Link href="/account/orders">My orders</Link></Button>
              <Button asChild><Link href="/products">Continue shopping</Link></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!order || (pollingPhase === "loading" && !orderId)) {
    return (
      <div className="space-y-4">
        <PageHeader title="Order status" description="Loading..." />
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const lastPayment = order.payments?.[order.payments.length - 1];
  const paymentStatus: PaymentStatus = (lastPayment?.status as PaymentStatus) ?? "pending";
  const config = paymentStatusConfig[paymentStatus] ?? paymentStatusConfig.pending;
  const Icon = config.icon;
  const isTerminal = TERMINAL_STATUSES.includes(paymentStatus);

  return (
    <div className="space-y-4">
      <PageHeader title="Order Confirmed" description={`Order #${order.id}`} />

      <Card className={config.bg}>
        <CardContent className="space-y-4 p-6">
          <Icon className={`h-12 w-12 ${config.color} ${paymentStatus === "pending" ? "animate-spin" : ""}`} />
          <div>
            <div className={`text-xl font-bold ${config.color.replace("600", "950")}`}>{config.label}</div>
            <p className={`mt-1 text-sm ${config.color.replace("600", "800")}`}>{config.description}</p>
          </div>
        </CardContent>
      </Card>

      {!isTerminal && (
        <Card>
          <CardContent className="flex items-center gap-3 p-4 text-sm text-zinc-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            Checking payment status...
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-3 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Order summary</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-zinc-500">Order number</div>
            <div className="font-medium text-right">#{order.id}</div>
            <div className="text-zinc-500">Payment status</div>
            <div className="font-medium text-right capitalize">{paymentStatus}</div>
            <div className="text-zinc-500">Total</div>
            <div className="font-medium text-right">
              {formatMoney(
                order.items.reduce((sum, it) => sum + (Number(it.price) * it.quantity), 0)
              )}
            </div>
            <div className="text-zinc-500">Items</div>
            <div className="font-medium text-right">{order.items.length}</div>
            {lastPayment?.provider && (
              <>
                <div className="text-zinc-500">Provider</div>
                <div className="font-medium text-right capitalize">{lastPayment.provider}</div>
              </>
            )}
            {lastPayment?.failure_reason && (
              <>
                <div className="text-zinc-500">Reason</div>
                <div className="font-medium text-right text-red-600">{lastPayment.failure_reason}</div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        {isTerminal && (
          <Button asChild>
            <Link href={`/account/orders/${order.id}`}>Track order</Link>
          </Button>
        )}
        {lastPayment?.status === "failed" && (
          <Button asChild>
            <Link href={`/account/orders/${order.id}`}>Retry payment</Link>
          </Button>
        )}
        <Button asChild variant="outline">
          <Link href="/products">Continue shopping</Link>
        </Button>
      </div>
    </div>
  );
}
