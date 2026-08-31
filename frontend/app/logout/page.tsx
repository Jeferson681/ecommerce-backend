"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { authService } from "@/modules/auth/services/authService";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    async function logout() {
      const refreshToken = tokenStorage.getRefreshToken();
      try {
        if (refreshToken) {
          await authService.logout(refreshToken);
        }
      } finally {
        tokenStorage.clear();
        router.replace("/");
      }
    }

    void logout();
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-sm text-zinc-600">Signing out...</div>
    </div>
  );
}
