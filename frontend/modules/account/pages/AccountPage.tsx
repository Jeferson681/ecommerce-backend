"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { cartStorage } from "@/modules/cart/storage/cartStorage";
import { useMe } from "@/modules/account/hooks/useMe";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

export default function AccountPage() {
  const token = tokenStorage.getAccessToken();
  const { data, isLoading, error } = useMe();

  if (!token) {
    return (
      <div className="space-y-4">
        <PageHeader title="Account" description="Sign in to view your profile" />
        <Card>
          <CardContent className="p-6 space-y-3">
            <p className="text-sm text-zinc-700">You are not signed in.</p>
            <div className="flex items-center gap-2">
              <Button asChild>
                <Link href="/login?next=/account">Sign in</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/signup">Create account</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  let content: ReactNode;

  if (isLoading) {
    content = (
      <div className="space-y-4">
        <div className="h-5 w-40 animate-pulse rounded bg-zinc-200" />
        <div className="h-4 w-60 animate-pulse rounded bg-zinc-200" />
        <div className="h-4 w-48 animate-pulse rounded bg-zinc-200" />
      </div>
    );
  } else if (data) {
    content = (
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs text-zinc-500">Name</dt>
          <dd className="text-sm font-medium">{data.first_name} {data.last_name}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Email</dt>
          <dd className="text-sm">{data.email}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Status</dt>
          <dd className="text-sm">{data.is_active ? "Active" : "Inactive"}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Created</dt>
          <dd className="text-sm">{new Date(data.created_at).toLocaleString()}</dd>
        </div>
      </dl>
    );
  } else {
    content = null;
  }

  return (
    <div className="space-y-4">
      <PageHeader title="My account" />

      {error ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4 text-sm text-amber-800">
            {getUserErrorMessage(error)}
          </CardContent>
        </Card>
      ) : !data && !isLoading ? (
        <Card>
          <CardContent className="p-6 text-sm text-zinc-600">
            Unable to load profile information.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-6">
            {content}
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2">
        <Button asChild>
          <Link href="/account/orders">My orders</Link>
        </Button>

        <Button
          variant="outline"
          onClick={() => {
            cartStorage.clear();
            tokenStorage.clear();
            location.href = "/";
          }}
        >
          Sign out
        </Button>
      </div>
    </div>
  );
}
