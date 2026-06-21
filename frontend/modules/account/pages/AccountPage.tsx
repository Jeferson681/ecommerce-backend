"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";

import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";

export default function AccountPage() {
  const hasToken = useSyncExternalStore(
    tokenStorage.subscribe,
    () => Boolean(tokenStorage.getAccessToken()),
    () => false
  );

  if (!hasToken) {
    return (
      <div className="space-y-4">
        <PageHeader title="My Account" description="Sign in to access your account" />
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-zinc-600 mb-4">You need to sign in to view your account.</p>
            <Link href="/login?next=/account" className="text-sm font-medium text-[#007185] hover:text-[#c7511f] hover:underline">
              Sign in
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="My Account" description="Manage your account and orders" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500 mb-2">Orders</h3>
            <p className="text-sm text-zinc-600 mb-4">View your order history and track deliveries.</p>
            <Link href="/account/orders" className="text-sm font-medium text-[#007185] hover:text-[#c7511f] hover:underline">
              View orders
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500 mb-2">Profile</h3>
            <p className="text-sm text-zinc-600 mb-4">Manage your personal information.</p>
            <Link href="/users/me" className="text-sm font-medium text-[#007185] hover:text-[#c7511f] hover:underline">
              Edit profile
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500 mb-2">Sign out</h3>
            <p className="text-sm text-zinc-600 mb-4">Sign out of your account.</p>
            <Link href="/logout" className="text-sm font-medium text-red-600 hover:text-red-700 hover:underline">
              Sign out
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
