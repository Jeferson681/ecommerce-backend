"use client";

import type { ReactNode } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Elements } from "@stripe/react-stripe-js";

import { STRIPE_PUBLISHABLE_KEY } from "@/core/config/stripe";

const stripePromise = loadStripe(STRIPE_PUBLISHABLE_KEY);

type StripeProviderProps = {
  children: ReactNode;
};

/**
 * Provides Stripe Elements context to the tree.
 * Must be wrapped around any component that uses useStripe / useElements.
 */
export function StripeProvider({ children }: StripeProviderProps) {
  if (!STRIPE_PUBLISHABLE_KEY) {
    return (
      <div className="rounded-sm border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Stripe is not configured. Set{" "}
        <code className="font-mono text-xs">NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY</code>{" "}
        in your environment.
      </div>
    );
  }

  return (
    <Elements stripe={stripePromise}>
      {children}
    </Elements>
  );
}
