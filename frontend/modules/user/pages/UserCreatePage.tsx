"use client";

import { useRouter } from "next/navigation";

import { userService } from "@/modules/user/services/userService";
import type { UserCreateInput } from "@/modules/user/types/user";

import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";
import { UserForm } from "@/modules/user/components/UserForm";

export default function UserCreatePage() {
  const router = useRouter();

  async function handleCreate(input: UserCreateInput) {
    await userService.create(input);
    router.push("/users?success=User%20created");
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Create user" description="Create a new user" />
      <Card>
        <CardContent className="p-6">
          <UserForm mode="create" onSubmit={handleCreate} />
        </CardContent>
      </Card>
    </div>
  );
}
