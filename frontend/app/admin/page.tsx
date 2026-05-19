import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";

export default function Page() {
  const adminEnabled = process.env.NEXT_PUBLIC_ENABLE_ADMIN === "true";
  if (!adminEnabled) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Admin" description="Backoffice (MVP stub)" />
      <Card>
        <CardContent className="p-6 space-y-2">
          <p className="text-sm text-zinc-700">Admin area is intentionally minimal for now.</p>
          <div className="text-sm">
            <Link href="/users" className="underline underline-offset-4">
              Manage users
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
