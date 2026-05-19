import Link from "next/link";

import type { Product } from "@/modules/product/types/product";
import { formatMoney } from "@/core/utils/money";
import { AddToCartButton } from "@/modules/cart/components/AddToCartButton";

import { Card, CardContent } from "@/shared/components/ui/card";

type ProductCardProps = {
  product: Product;
  compact?: boolean;
};

export function ProductCard({ product, compact = false }: ProductCardProps) {
  return (
    <Card className="group overflow-hidden border-zinc-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg">
      <div className="bg-gradient-to-br from-amber-100 via-orange-50 to-white px-5 py-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <span className="inline-flex rounded-full bg-zinc-950 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-white">
              New
            </span>
            <h3 className="text-lg font-semibold leading-tight text-zinc-950">
              <Link href={`/products/${product.id}`} className="hover:underline underline-offset-4">
                {product.name}
              </Link>
            </h3>
          </div>
          <div className="rounded-2xl bg-white/80 px-3 py-2 text-right shadow-sm ring-1 ring-zinc-200">
            <div className="text-xs text-zinc-500">Price</div>
            <div className="text-lg font-semibold text-zinc-950">{formatMoney(product.price)}</div>
          </div>
        </div>
      </div>
      <CardContent className="space-y-4 p-5">
        <p className={`text-sm text-zinc-600 ${compact ? "line-clamp-2" : "line-clamp-3"}`}>
          {product.description ?? "No description available."}
        </p>
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs font-medium text-zinc-500">Stock {product.stock_quantity}</span>
          <AddToCartButton product={product} label="Add" className="h-9 rounded-full px-4" />
        </div>
      </CardContent>
    </Card>
  );
}
