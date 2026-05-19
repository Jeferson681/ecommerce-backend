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

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  const productId = Number(id);

  if (!Number.isInteger(productId)) {
    return (
      <div className="space-y-4">
        <PageHeader title="Product" description="Invalid product id" />
        <div className="text-sm">
          <Link href="/products" className="underline underline-offset-4">
            Back to products
          </Link>
        </div>
      </div>
    );
  }

  let product: Awaited<ReturnType<typeof productService.get>> | null = null;
  let loadError: string | null = null;
  try {
    product = await productService.get(productId);
  } catch (err) {
    product = null;
    loadError = err instanceof Error ? err.message : "Failed to load product";
  }

  if (!product) {
    return (
      <div className="space-y-4">
        <PageHeader title="Product" description="Unavailable" />
        {loadError ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            Product backend is unavailable right now. ({loadError})
          </div>
        ) : (
          <div className="text-sm text-zinc-600">Product not found.</div>
        )}
        <div className="text-sm">
          <Link href="/products" className="underline underline-offset-4">
            Back to products
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={product.name} description="Product details" />

      <Card>
        <CardContent className="p-6 space-y-3">
          <div className="text-lg font-semibold">{formatPrice(product.price)}</div>
          <div className="text-sm text-zinc-700">{product.description ?? "No description."}</div>
          <div className="text-xs text-zinc-500">Stock: {product.stock_quantity}</div>
        </CardContent>
      </Card>

      <div className="text-sm">
        <Link href="/products" className="underline underline-offset-4">
          Back to products
        </Link>
      </div>
    </div>
  );
}
