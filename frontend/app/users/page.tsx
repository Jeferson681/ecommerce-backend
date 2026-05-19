import { Suspense } from "react";

import UsersListPage from "@/modules/user/pages/UsersListPage";

export default function Page() {
  return (
    <Suspense fallback={<div className="text-sm text-zinc-600">Loading...</div>}>
      <UsersListPage />
    </Suspense>
  );
}
