import Link from "next/link";
import { ChevronLeft, ShieldCheck, Truck, Star } from "lucide-react";

import { formatMoney } from "@/core/utils/money";
import { productService } from "@/modules/product/services/productService";
import { AddToCartButton } from "@/modules/cart/components/AddToCartButton";
import { ProductCard } from "@/modules/product/components/ProductCard";
import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";

type ProductPageProps = {
  productId: number;
};

export default async function ProductPage({ productId }: ProductPageProps) {
  let product: Awaited<ReturnType<typeof productService.get>> | null = null;
  let products: Awaited<ReturnType<typeof productService.list>> = [];
  let loadError: string | null = null;

  try {
    product = await productService.get(productId);
    products = await productService.list();
  } catch (err) {
    product = null;
    products = [];
    loadError = err instanceof Error ? err.message : "Failed to load product";
  }

  if (!product) {
    return (
      <div className="space-y-6">
        <Button asChild variant="ghost" className="w-fit rounded-full px-0 text-zinc-700">
          <Link href="/products">
            <ChevronLeft className="h-4 w-4" /> Back to catalog
          </Link>
        </Button>

        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Product backend is unavailable right now. ({loadError ?? "Unavailable"})
        </div>
      </div>
    );
  }
  const related = products.filter((item) => item.is_active && item.id !== product.id).slice(0, 3);

  return (
    <div className="space-y-8">
      <Button asChild variant="ghost" className="w-fit rounded-full px-0 text-zinc-700">
        <Link href="/products">
          <ChevronLeft className="h-4 w-4" /> Back to catalog
        </Link>
      </Button>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="overflow-hidden border-zinc-200 bg-white shadow-sm">
          <div className="bg-gradient-to-br from-amber-100 via-orange-50 to-white p-8">
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.24em] text-zinc-500">
              <span className="rounded-full bg-white px-3 py-1 font-semibold text-zinc-700">Marketplace</span>
              <span className="rounded-full bg-zinc-950 px-3 py-1 font-semibold text-white">{product.is_active ? "Active" : "Hidden"}</span>
            </div>
            <PageHeader title={product.name} description={product.description ?? "No description."} />
            <div className="mt-5 flex flex-wrap items-center gap-4">
              <div className="text-4xl font-black tracking-tight text-zinc-950">{formatMoney(product.price)}</div>
              <div className="rounded-full bg-white px-4 py-2 text-sm font-medium text-zinc-600 shadow-sm ring-1 ring-zinc-200">
                Stock {product.stock_quantity}
              </div>
            </div>
          </div>
          <CardContent className="space-y-5 p-6">
            <p className="text-sm leading-7 text-zinc-600">
              A polished product page with trust badges, product info and a clear call to action. Perfect for
              marketplace-style storefronts.
            </p>
            <div className="flex flex-wrap gap-3">
              <AddToCartButton product={product} quantity={1} className="rounded-full px-6" />
              <Button asChild variant="outline" className="rounded-full px-6">
                <Link href="/checkout">Checkout</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-zinc-200 bg-white shadow-sm">
          <CardContent className="space-y-4 p-6">
            <div className="text-sm font-semibold uppercase tracking-[0.22em] text-zinc-500">Why customers buy</div>
            {[
              { icon: Truck, title: "Fast shipping", text: "Layout supports delivery and pickup messaging." },
              { icon: ShieldCheck, title: "Secure checkout", text: "Use the frontend checkout without backend changes." },
              { icon: Star, title: "Trusted product", text: "Clear pricing and stock information help conversion." },
            ].map((item) => (
              <div key={item.title} className="flex items-start gap-3 rounded-2xl border border-zinc-200 p-4">
                <item.icon className="mt-0.5 h-5 w-5 text-zinc-950" />
                <div>
                  <div className="text-sm font-semibold text-zinc-950">{item.title}</div>
                  <div className="mt-1 text-sm leading-6 text-zinc-600">{item.text}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      {related.length > 0 ? (
        <section className="space-y-4">
          <PageHeader title="Related items" description="Products customers may also like" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {related.map((item) => (
              <ProductCard key={item.id} product={item} compact />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
