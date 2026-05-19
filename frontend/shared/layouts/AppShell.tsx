import Link from "next/link";

import { cn } from "@/core/utils/cn";
import { AuthNav } from "@/shared/components/AuthNav";
import { CartButton } from "@/modules/cart/components/CartButton";
import { SearchBar } from "@/shared/components/SearchBar";

type AppShellProps = {
  children: React.ReactNode;
  title?: string;
};

export function AppShell({ children, title = "Mercado" }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(251,191,36,0.18),transparent_25%),linear-gradient(to_bottom,#fff8ee,#ffffff_30%,#fafafa)] text-zinc-950">
      <div className="border-b border-zinc-900 bg-zinc-950 px-4 py-2 text-center text-xs font-medium text-white">
        Free shipping on orders over $50. Fast checkout.
      </div>
      <header className="sticky top-0 z-30 border-b border-zinc-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-6">
            <div className="flex items-center justify-between gap-4">
              <Link href="/" className="text-xl font-black tracking-tight text-zinc-950">
                {title}
              </Link>
              <div className="flex items-center gap-2 lg:hidden">
                <CartButton />
                <AuthNav />
              </div>
            </div>

            <div className="flex-1 lg:max-w-2xl">
              <SearchBar />
            </div>

            <div className="hidden items-center gap-2 lg:flex">
              <CartButton />
              <AuthNav />
            </div>
          </div>

          <nav className="mt-4 flex gap-2 overflow-x-auto pb-1 text-sm font-medium text-zinc-700">
            {[
              ["Home", "/"],
              ["Catalog", "/products"],
              ["Cart", "/cart"],
              ["Checkout", "/checkout"],
            ].map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "whitespace-nowrap rounded-full border border-zinc-200 bg-white px-4 py-2 shadow-sm transition hover:border-zinc-300 hover:bg-zinc-50"
                )}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">{children}</main>
      <footer className="border-t border-zinc-200 bg-white/80">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-2 px-4 py-8 text-sm text-zinc-600 sm:flex-row sm:items-center sm:justify-between">
          <p>Marketplace storefront MVP</p>
          <p>Built on top of the existing backend endpoints.</p>
        </div>
      </footer>
    </div>
  );
}
