"use client";

import Link from "next/link";
import { ShoppingCart } from "lucide-react";

import { useCart } from "@/modules/cart/hooks/useCart";

export function CartButton() {
  const { itemCount } = useCart();

  return (
    <Link
      href="/cart"
      className="relative flex items-center gap-1 px-2 py-1 text-white/90 hover:text-white transition-colors"
    >
      <div className="relative">
        <ShoppingCart className="h-5 w-5" />
        {itemCount > 0 ? (
          <span className="absolute -right-2 -top-2 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[#febd69] px-1 text-[10px] font-bold text-[#131921] leading-none">
            {itemCount > 99 ? "99+" : itemCount}
          </span>
        ) : null}
      </div>
      <span className="hidden text-[11px] font-medium leading-tight lg:flex lg:flex-col">
        <span className="text-[10px] text-zinc-400">Cart</span>
        <span className="text-[13px] font-bold text-white">{itemCount} item{itemCount !== 1 ? "s" : ""}</span>
      </span>
    </Link>
  );
}
