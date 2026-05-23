import Link from "next/link";

import { AuthNav } from "@/shared/components/AuthNav";
import { CartButton } from "@/modules/cart/components/CartButton";
import { SearchBar } from "@/shared/components/SearchBar";
import { CategoryNav } from "@/shared/components/CategoryNav";

type AppShellProps = {
  children: React.ReactNode;
  title?: string;
};

export function AppShell({ children, title = "Mercado" }: AppShellProps) {
  return (
    <div className="min-h-screen bg-zinc-100 text-zinc-900">
      {/* Top announcement bar - Amazon style */}
      <div className="bg-[#131921] px-4 py-1.5 text-center text-[11px] font-medium tracking-wide text-[#febd69]">
        <span className="inline-block">
          <span className="text-white/70">🚚 Free shipping on orders over $50.</span> Fast checkout.
        </span>
      </div>

      {/* Main header - Amazon style dark nav */}
      <header className="sticky top-0 z-50 bg-[#131921] shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-2.5">
          {/* Logo */}
          <Link
            href="/"
            className="flex shrink-0 items-baseline gap-0 no-underline"
          >
            <span className="text-xl font-bold tracking-tight text-white">
              {title}
            </span>
            <span className="ml-1 text-[10px] font-light text-[#febd69]">
              .com
            </span>
          </Link>

          {/* Search bar - centered, takes remaining space */}
          <div className="flex-1 group">
            <SearchBar />
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-1">
            <AuthNav />
            <CartButton />
          </div>
        </div>
      </header>

      {/* Category navigation bar - Amazon style */}
      <CategoryNav />

      {/* Breadcrumb area */}
      <div className="mx-auto max-w-7xl px-4 pt-3">
        <Breadcrumbs />
      </div>

      {/* Main content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-4">
        {children}
      </main>

      {/* Footer */}
      <footer className="mt-8 border-t border-zinc-300 bg-white">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-1 px-4 py-6 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 {title}. All rights reserved.</p>
          <p className="text-zinc-400">Marketplace storefront</p>
        </div>
      </footer>
    </div>
  );
}

function Breadcrumbs() {
  return (
    <nav className="flex items-center gap-1.5 text-xs text-zinc-500" aria-label="Breadcrumb">
      <Link href="/" className="hover:text-zinc-800 transition-colors">
        Home
      </Link>
      <span className="text-zinc-300 mx-0.5">›</span>
      <Link href="/products" className="hover:text-zinc-800 transition-colors">
        Products
      </Link>
    </nav>
  );
}
