"use client";

import { useRouter } from "next/navigation";

import { useUser } from "@/modules/user/hooks/useUser";
import { userService } from "@/modules/user/services/userService";
import type { UserUpdateInput } from "@/modules/user/types/user";

import { PageHeader } from "@/shared/components/PageHeader";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Card, CardContent } from "@/shared/components/ui/card";
import { UserForm } from "@/modules/user/components/UserForm";

type UserEditPageProps = {
  userId: number;
};

export default function UserEditPage({ userId }: UserEditPageProps) {
  const router = useRouter();
  const { data, isLoading, error } = useUser(userId);

  async function handleUpdate(input: UserUpdateInput) {
    await userService.update(userId, input);
    router.push(`/users/${userId}?success=User%20updated`);
  }

  return (
    <div className="space-y-4">
      <PageHeader title={`Edit user #${userId}`} description="Update user fields" />

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
            <UserForm mode="edit" initial={data} onSubmit={handleUpdate} submitLabel="Save" />
          ) : (
            <div className="text-sm text-zinc-600">Not found.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
