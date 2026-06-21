"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";

import { tokenStorage } from "@/modules/auth/storage/tokenStorage";

export function AuthNav() {
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  if (!hasToken) {
    return (
      <div className="flex items-center gap-3">
        <Link
          href="/login"
          className="text-xs text-white/80 hover:text-white transition-colors"
        >
          Sign in
        </Link>
        <Link
          href="/signup"
          className="text-xs text-white/80 hover:text-white transition-colors"
        >
          Sign up
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Link
        href="/account"
        className="text-xs text-white/80 hover:text-white transition-colors"
      >
        My Account
      </Link>
      <Link
        href="/logout"
        className="text-xs text-zinc-400 hover:text-red-400 transition-colors"
      >
        Sign out
      </Link>
    </div>
  );
}
