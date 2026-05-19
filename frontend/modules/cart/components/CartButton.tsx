"use client";

import Link from "next/link";

import { useCart } from "@/modules/cart/hooks/useCart";

import { Button } from "@/shared/components/ui/button";

export function CartButton() {
  const { itemCount } = useCart();

  return (
    <Button asChild variant="outline" size="sm" className="relative">
      <Link href="/cart">
        Cart
        {itemCount > 0 ? (
          <span className="ml-1 rounded-full bg-zinc-950 px-2 py-0.5 text-[11px] font-semibold text-white">
            {itemCount}
          </span>
        ) : null}
      </Link>
    </Button>
  );
}
