"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";

import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { cartStorage } from "@/modules/cart/storage/cartStorage";

import { Button } from "@/shared/components/ui/button";

export function AuthNav() {
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  if (hasToken) {
    return (
      <div className="flex items-center gap-2">
        <Button asChild variant="ghost" size="sm">
          <Link href="/account">Account</Link>
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            cartStorage.clear();
            tokenStorage.clear();
            location.href = "/";
          }}
        >
          Sign out
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Button asChild variant="ghost" size="sm">
        <Link href="/login?next=/account">Sign in</Link>
      </Button>
      <Button asChild size="sm">
        <Link href="/signup">Sign up</Link>
      </Button>
    </div>
  );
}
