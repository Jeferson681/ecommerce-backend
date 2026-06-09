"use client";

import { useState } from "react";
import Link from "next/link";

import { useUser } from "@/modules/user/hooks/useUser";
import { userService } from "@/modules/user/services/userService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

import { PageHeader } from "@/shared/components/PageHeader";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";

type UserDetailPageProps = {
  userId: number;
};

export default function UserDetailPage({ userId }: UserDetailPageProps) {
  const { data, isLoading, error, refetch } = useUser(userId);
  const [toggleOpen, setToggleOpen] = useState(false);
  const [isToggling, setIsToggling] = useState(false);
  const [toggleError, setToggleError] = useState<string | null>(null);

  async function handleToggleActive() {
    if (!data) return;
    setIsToggling(true);
    setToggleError(null);
    try {
      await userService.update(userId, { is_active: !data.is_active });
      setToggleOpen(false);
      await refetch();
    } catch (err) {
      setToggleError(getUserErrorMessage(err));
    } finally {
      setIsToggling(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title={isLoading ? "User" : data ? `User #${data.id}` : "User"}
        description="View user details"
        action={
          <div className="flex items-center gap-2">
            {data ? (
              <Button
                variant={data.is_active ? "destructive" : "default"}
                size="sm"
                onClick={() => {
                  setToggleError(null);
                  setToggleOpen(true);
                }}
              >
                {data.is_active ? "Deactivate" : "Activate"}
              </Button>
            ) : null}
            <Button asChild variant="secondary" size="sm">
              <Link href={`/users/${userId}/edit`}>Edit</Link>
            </Button>
          </div>
        }
      />

      {toggleError ? (
        <Alert className="border-red-200">
          <AlertTitle>Action failed</AlertTitle>
          <AlertDescription>{toggleError}</AlertDescription>
        </Alert>
      ) : null}

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

      <div className="flex items-center gap-2">
        <Button asChild variant="outline">
          <Link href="/users">Back</Link>
        </Button>
      </div>

      {/* Confirmation dialog for activating/deactivating user */}
      <Dialog open={toggleOpen} onOpenChange={setToggleOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{data?.is_active ? "Deactivate user" : "Activate user"}</DialogTitle>
            <DialogDescription>
              {data?.is_active
                ? `This will deactivate ${data?.first_name ?? ""} ${data?.last_name ?? ""}. The user will lose access to their account.`
                : `This will activate ${data?.first_name ?? ""} ${data?.last_name ?? ""}. The user will regain access to their account.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={isToggling}>
                Cancel
              </Button>
            </DialogClose>
            <Button
              variant={data?.is_active ? "destructive" : "default"}
              onClick={handleToggleActive}
              disabled={isToggling}
            >
              {isToggling ? "Saving..." : data?.is_active ? "Deactivate" : "Activate"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
