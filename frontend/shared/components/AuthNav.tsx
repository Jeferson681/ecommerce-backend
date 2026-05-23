"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import { ChevronDown } from "lucide-react";

import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { cartStorage } from "@/modules/cart/storage/cartStorage";

export function AuthNav() {
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  if (hasToken) {
    return (
      <div className="flex items-center">
        <Link
          href="/account"
          className="flex flex-col px-2 py-1 text-white/90 hover:text-white transition-colors"
        >
          <span className="text-[10px] text-zinc-400 leading-none">Account</span>
          <span className="text-[13px] font-bold leading-tight">
            My Account <ChevronDown className="inline h-3 w-3" />
          </span>
        </Link>
        <button
          className="px-2 py-1 text-[11px] text-zinc-400 hover:text-white transition-colors"
          onClick={() => {
            cartStorage.clear();
            tokenStorage.clear();
            location.href = "/";
          }}
        >
          Sign Out
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center">
      <Link
        href="/login?next=/account"
        className="flex flex-col px-2 py-1 text-white/90 hover:text-white transition-colors"
      >
        <span className="text-[10px] text-zinc-400 leading-none">Hello, Sign in</span>
        <span className="text-[13px] font-bold leading-tight">
          Account & Lists <ChevronDown className="inline h-3 w-3" />
        </span>
      </Link>
      <Link
        href="/signup"
        className="flex flex-col px-2 py-1 text-white/90 hover:text-white transition-colors"
      >
        <span className="text-[10px] text-zinc-400 leading-none">New customer?</span>
        <span className="text-[13px] font-bold leading-tight">Start here</span>
      </Link>
    </div>
  );
}
