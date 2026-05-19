import { Suspense } from "react";

import LoginPage from "@/modules/auth/pages/LoginPage";

export default function Page() {
  return (
    <Suspense fallback={<div className="text-sm text-zinc-600">Loading...</div>}>
      <LoginPage />
    </Suspense>
  );
}
