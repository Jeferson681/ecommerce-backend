"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { ApiError } from "@/core/exceptions/ApiError";
import { userService } from "@/modules/user/services/userService";
import { useUsers } from "@/modules/user/hooks/useUsers";
import type { User } from "@/modules/user/types/user";

import { PageHeader } from "@/shared/components/PageHeader";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { UserTable } from "@/modules/user/components/UserTable";
import { UserDeleteDialog } from "@/modules/user/components/UserDeleteDialog";

export default function UsersListPage() {
  const { data, isLoading, error, refetch } = useUsers();
  const searchParams = useSearchParams();
  const success = searchParams.get("success");

  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const sorted = useMemo(() => {
    return (data ?? []).slice().sort((a, b) => a.id - b.id);
  }, [data]);

  function askDelete(user: User) {
    setDeleteError(null);
    setDeleteTarget(user);
    setIsDeleteOpen(true);
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await userService.delete(deleteTarget.id);
      setIsDeleteOpen(false);
      setDeleteTarget(null);
      await refetch();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to delete";
      setDeleteError(message);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Users"
        description="CRUD UI aligned with the backend user module"
        action={
          <Button asChild>
            <Link href="/users/new">Create user</Link>
          </Button>
        }
      />

      {success ? (
        <Alert className="border-green-200">
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      ) : null}

      {deleteError ? (
        <Alert className="border-red-200">
          <AlertTitle>Delete failed</AlertTitle>
          <AlertDescription>{deleteError}</AlertDescription>
        </Alert>
      ) : null}

      {error ? (
        <Alert className="border-red-200">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-zinc-600">Loading users...</div>
          ) : sorted.length === 0 ? (
            <div className="p-6 text-sm text-zinc-600">No users found.</div>
          ) : (
            <div className="p-4">
              <UserTable users={sorted} onDelete={askDelete} />
            </div>
          )}
        </CardContent>
      </Card>

      <UserDeleteDialog
        user={deleteTarget}
        isOpen={isDeleteOpen}
        isDeleting={isDeleting}
        onOpenChange={setIsDeleteOpen}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
