import Link from "next/link";

import { productService } from "@/modules/product/services/productService";
import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";

function formatPrice(value: string) {
  const numberValue = Number(value);
  if (Number.isFinite(numberValue)) {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(numberValue);
  }
  return value;
}

export default async function Page() {
  let products: Awaited<ReturnType<typeof productService.list>> = [];
  let loadError: string | null = null;

  try {
    products = await productService.list();
  } catch (err) {
    products = [];
    loadError = err instanceof Error ? err.message : "Failed to load products";
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Products" description="Browse our catalog" />

      {loadError ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Products backend is unavailable right now. ({loadError})
        </div>
      ) : null}

      {products.length === 0 ? (
        <div className="text-sm text-zinc-600">No products yet.</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products
            .filter((p) => p.is_active)
            .map((p) => (
              <Card key={p.id} className="hover:shadow-sm transition-shadow">
                <CardContent className="p-5 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold leading-tight">
                        <Link href={`/products/${p.id}`} className="underline-offset-4 hover:underline">
                          {p.name}
                        </Link>
                      </h3>
                      {p.description ? (
                        <p className="mt-1 text-sm text-zinc-600 line-clamp-3">{p.description}</p>
                      ) : (
                        <p className="mt-1 text-sm text-zinc-400">No description.</p>
                      )}
                    </div>
                    <div className="text-sm font-medium text-zinc-900 whitespace-nowrap">{formatPrice(p.price)}</div>
                  </div>
                  <div className="text-xs text-zinc-500">Stock: {p.stock_quantity}</div>
                </CardContent>
              </Card>
            ))}
        </div>
      )}
    </div>
  );
}
