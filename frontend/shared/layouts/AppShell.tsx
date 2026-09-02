"use client";

import Link from "next/link";

import { AuthNav } from "@/shared/components/AuthNav";
import { CartButton } from "@/modules/cart/components/CartButton";
import { SearchBar } from "@/shared/components/SearchBar";
import { CategoryNav } from "@/shared/components/CategoryNav";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-zinc-100 text-zinc-900">
      {/* Announcement bar */}
      <div className="bg-[#131921] px-4 py-1 text-center text-[11px] text-white/70">
        Free shipping on orders over $50. Fast checkout.
      </div>

      {/* Main header */}
      <header className="sticky top-0 z-50 bg-[#131921]">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2">
          <Link href="/" className="flex shrink-0 items-baseline gap-0 no-underline">
            <span className="text-lg font-bold tracking-tight text-white">Storefront</span>
            <span className="ml-0.5 text-[10px] text-[#febd69]">.com</span>
          </Link>

          <div className="flex-1">
            <SearchBar />
          </div>

          <div className="flex items-center gap-2">
            <AuthNav />
            <CartButton />
          </div>
        </div>
      </header>

      <CategoryNav />

      {/* Main content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-4">
        {children}
      </main>

      {/* Footer */}
      <footer className="mt-8 border-t border-zinc-300 bg-white">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-1 px-4 py-6 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; 2026 Storefront. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
