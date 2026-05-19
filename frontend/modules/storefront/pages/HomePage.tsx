import Link from "next/link";
import { ChevronRight, ShieldCheck, Truck } from "lucide-react";

import { productService } from "@/modules/product/services/productService";
import { ProductCard } from "@/modules/product/components/ProductCard";
import { SearchBar } from "@/shared/components/SearchBar";
import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

export default async function HomePage() {
  let products: Awaited<ReturnType<typeof productService.list>> = [];
  try {
    products = await productService.list();
  } catch {
    products = [];
  }
  const featured = products.filter((product) => product.is_active).slice(0, 4);

  return (
    <div className="space-y-10">
      <section className="overflow-hidden rounded-[2rem] border border-amber-200 bg-gradient-to-br from-amber-50 via-white to-orange-50 shadow-sm">
        <div className="grid gap-10 px-6 py-10 lg:grid-cols-[1.15fr_0.85fr] lg:px-10 lg:py-14">
          <div className="space-y-6">
            <div className="inline-flex rounded-full bg-zinc-950 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-white">
              Marketplace ready
            </div>
            <div className="space-y-3">
              <h1 className="max-w-2xl text-4xl font-black tracking-tight text-zinc-950 sm:text-5xl">
                Everything your store needs, styled like a real marketplace.
              </h1>
              <p className="max-w-xl text-base leading-7 text-zinc-600">
                Homepage, catalog, search, product pages, cart and checkout with a clean Amazon/Mercado Livre style.
              </p>
            </div>

            <div className="max-w-xl">
              <SearchBar />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg" className="rounded-full px-6">
                <Link href="/products">
                  Browse catalog <ChevronRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="rounded-full px-6">
                <Link href="/cart">View cart</Link>
              </Button>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { icon: Truck, title: "Fast delivery", text: "Delivery-ready layout for store ops." },
                { icon: ShieldCheck, title: "Secure flow", text: "Checkout and auth UX kept simple." },
                {
                  icon: ChevronRight,
                  title: "Backend-ready",
                  text: "Prepared for future backend modules without breaking the storefront.",
                },
              ].map((item) => (
                <Card key={item.title} className="border-zinc-200/80 bg-white/80 backdrop-blur">
                  <CardContent className="p-4">
                    <item.icon className="h-5 w-5 text-zinc-950" />
                    <div className="mt-3 text-sm font-semibold text-zinc-950">{item.title}</div>
                    <div className="mt-1 text-sm text-zinc-600">{item.text}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-center">
            <div className="grid w-full max-w-md gap-4 rounded-[1.75rem] bg-zinc-950 p-4 text-white shadow-2xl shadow-zinc-950/20">
              <div className="rounded-[1.5rem] bg-white/10 p-4">
                <div className="text-xs uppercase tracking-[0.3em] text-amber-200">Today&apos;s deal</div>
                <div className="mt-3 text-2xl font-bold leading-tight">Fresh picks with marketplace energy</div>
                <p className="mt-2 text-sm text-zinc-300">
                  A visual direction inspired by Amazon, Mercado Livre, Americanas and Shopify storefronts.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-[1.25rem] bg-white/10 p-4">
                  <div className="text-3xl font-black">24h</div>
                  <div className="text-xs uppercase tracking-[0.2em] text-zinc-400">shipping vibe</div>
                </div>
                <div className="rounded-[1.25rem] bg-amber-400 p-4 text-zinc-950">
                  <div className="text-3xl font-black">1k+</div>
                  <div className="text-xs uppercase tracking-[0.2em]">products ready</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <PageHeader title="Featured products" description="Highlights from the live catalog" />
        {featured.length === 0 ? (
          <div className="text-sm text-zinc-600">No products available yet.</div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {featured.map((product) => (
              <ProductCard key={product.id} product={product} compact />
            ))}
          </div>
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2 border-zinc-200 bg-zinc-950 text-white">
          <CardContent className="flex h-full flex-col justify-between gap-5 p-6">
            <div>
              <div className="text-sm font-medium uppercase tracking-[0.22em] text-amber-200">Storefront</div>
              <h2 className="mt-3 text-2xl font-bold">Catalog, search and product detail are all connected.</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-300">
                The frontend now feels like a real ecommerce experience while still respecting your current backend.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild variant="secondary" className="rounded-full">
                <Link href="/products">Open catalog</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-full border-white/20 bg-transparent text-white hover:bg-white/10">
                <Link href="/checkout">Go to checkout</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
