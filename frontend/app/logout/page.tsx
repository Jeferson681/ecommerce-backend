"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    tokenStorage.clear();
    router.push("/");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-sm text-zinc-600">Signing out...</div>
    </div>
  );
}
