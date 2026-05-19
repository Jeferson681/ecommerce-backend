"use client";

import Link from "next/link";

import { useUser } from "@/modules/user/hooks/useUser";

import { PageHeader } from "@/shared/components/PageHeader";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

type UserDetailPageProps = {
  userId: number;
};

export default function UserDetailPage({ userId }: UserDetailPageProps) {
  const { data, isLoading, error } = useUser(userId);

  return (
    <div className="space-y-4">
      <PageHeader
        title={isLoading ? "User" : data ? `User #${data.id}` : "User"}
        description="View user details"
        action={
          <Button asChild variant="secondary">
            <Link href={`/users/${userId}/edit`}>Edit</Link>
          </Button>
        }
      />

      {error ? (
        <Alert className="border-red-200">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardContent className="p-6">
          {isLoading ? (
            <div className="text-sm text-zinc-600">Loading...</div>
          ) : data ? (
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-xs text-zinc-500">First name</dt>
                <dd className="text-sm font-medium">{data.first_name}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Last name</dt>
                <dd className="text-sm font-medium">{data.last_name}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Email</dt>
                <dd className="text-sm">{data.email}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Created</dt>
                <dd className="text-sm">{new Date(data.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Status</dt>
                <dd className="text-sm">{data.is_active ? "Active" : "Inactive"}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Updated</dt>
                <dd className="text-sm">{new Date(data.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          ) : (
            <div className="text-sm text-zinc-600">Not found.</div>
          )}
        </CardContent>
      </Card>

      <Button asChild variant="outline">
        <Link href="/users">Back</Link>
      </Button>
    </div>
  );
}
