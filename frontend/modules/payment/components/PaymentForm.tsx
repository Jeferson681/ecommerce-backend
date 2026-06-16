"use client";

import { useState } from "react";
import {
  useStripe,
  useElements,
  CardNumberElement,
  CardExpiryElement,
  CardCvcElement,
} from "@stripe/react-stripe-js";
import type {
  StripeCardNumberElementChangeEvent,
  StripeCardExpiryElementChangeEvent,
  StripeCardCvcElementChangeEvent,
} from "@stripe/stripe-js";

import { Button } from "@/shared/components/ui/button";

type PaymentFormProps = {
  /** Called once the Stripe token / payment_method_id is ready. */
  onPaymentMethodReady: (paymentMethodId: string) => void;
  /** Called when the user decides to go back to cart. */
  onBack?: () => void;
  disabled?: boolean;
};

const inputClasses =
  "block w-full rounded-sm border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 outline-none";

/**
 * Stripe Card Element form.
 *
 * Collects card details via Stripe Elements, obtains a
 * `payment_method_id`, and passes it up so the parent can
 * send it to the backend.
 */
export function PaymentForm({
  onPaymentMethodReady,
  onBack,
  disabled,
}: PaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();

  const [errors, setErrors] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [cardComplete, setCardComplete] = useState(false);
  const [expiryComplete, setExpiryComplete] = useState(false);
  const [cvcComplete, setCvcComplete] = useState(false);

  const allComplete = cardComplete && expiryComplete && cvcComplete;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!stripe || !elements || !allComplete) return;

    setSubmitting(true);
    setErrors(null);

    const cardElement = elements.getElement(CardNumberElement);
    if (!cardElement) {
      setErrors("Card element not available.");
      setSubmitting(false);
      return;
    }

    const { error, paymentMethod } = await stripe.createPaymentMethod({
      type: "card",
      card: cardElement,
    });

    if (error) {
      setErrors(error.message ?? "An error occurred while processing your card.");
      setSubmitting(false);
      return;
    }

    onPaymentMethodReady(paymentMethod.id);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Card number */}
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700">
          Card number
        </label>
        <CardNumberElement
          options={{
            style: {
              base: {
                fontSize: "14px",
                fontFamily: "inherit",
                color: "#18181b",
                "::placeholder": { color: "#a1a1aa" },
              },
            },
            placeholder: "4242 4242 4242 4242",
          }}
          className={inputClasses}
          onChange={(e: StripeCardNumberElementChangeEvent) =>
            setCardComplete(e.complete)
          }
        />
      </div>

      {/* Expiry + CVC */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700">
            Expiry date
          </label>
          <CardExpiryElement
            options={{
              style: {
                base: {
                  fontSize: "14px",
                  fontFamily: "inherit",
                  color: "#18181b",
                  "::placeholder": { color: "#a1a1aa" },
                },
              },
              placeholder: "MM / YY",
            }}
            className={inputClasses}
            onChange={(e: StripeCardExpiryElementChangeEvent) =>
              setExpiryComplete(e.complete)
            }
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700">
            CVC
          </label>
          <CardCvcElement
            options={{
              style: {
                base: {
                  fontSize: "14px",
                  fontFamily: "inherit",
                  color: "#18181b",
                  "::placeholder": { color: "#a1a1aa" },
                },
              },
              placeholder: "123",
            }}
            className={inputClasses}
            onChange={(e: StripeCardCvcElementChangeEvent) =>
              setCvcComplete(e.complete)
            }
          />
        </div>
      </div>

      {errors && (
        <p className="text-sm text-red-600" role="alert">
          {errors}
        </p>
      )}

      <div className="flex items-center gap-2">
        {onBack && (
          <Button
            type="button"
            variant="outline"
            onClick={onBack}
            disabled={submitting || disabled}
          >
            Back
          </Button>
        )}
        <Button
          type="submit"
          disabled={!stripe || !allComplete || submitting || disabled}
          className="w-full rounded-sm bg-[#ffd814] text-sm font-medium text-[#111] hover:bg-[#f7ca00] border-0"
        >
          {submitting ? "Processing..." : "Pay with card"}
        </Button>
      </div>
    </form>
  );
}
