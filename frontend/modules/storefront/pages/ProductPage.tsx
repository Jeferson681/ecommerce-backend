import Link from "next/link";
import { ChevronLeft, Star } from "lucide-react";

import { productService } from "@/modules/product/services/productService";
import { AddToCartButton } from "@/modules/cart/components/AddToCartButton";
import { ProductCard } from "@/modules/product/components/ProductCard";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

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
    loadError = getUserErrorMessage(err);
  }

  if (!product) {
    return (
      <div className="space-y-4">
        <Link href="/products" className="inline-flex items-center gap-1 text-xs text-[#007185] hover:text-[#c7511f] hover:underline">
          <ChevronLeft className="h-3 w-3" /> Back to results
        </Link>
        <div className="rounded-sm border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900">
          Product unavailable. ({loadError ?? "Unavailable"})
        </div>
      </div>
    );
  }

  const related = products.filter((item) => item.is_active && item.id !== product.id).slice(0, 6);
  const stars = (3.5 + ((product.id * 17) % 15) / 10).toFixed(1);
  const reviewCount = ((product.id * 31 + 5) % 500) + 10;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-zinc-500" aria-label="Breadcrumb">
        <Link href="/" className="hover:text-zinc-800 transition-colors">Home</Link>
        <span className="text-zinc-300 mx-0.5">›</span>
        <Link href="/products" className="hover:text-zinc-800 transition-colors">All Products</Link>
        <span className="text-zinc-300 mx-0.5">›</span>
        <span className="text-zinc-800 font-medium truncate max-w-[200px]">{product.name}</span>
      </nav>

      {/* Product detail - Amazon-style two column */}
      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        {/* Image column */}
        <div className="aspect-square rounded-sm border border-zinc-200 bg-white flex items-center justify-center p-8">
          {product.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-contain"
            />
          ) : (
            <div className="text-center">
              <div className="mx-auto mb-3 h-24 w-24 rounded-full bg-zinc-100 flex items-center justify-center">
                <span className="text-4xl font-bold text-zinc-300">{product.name.charAt(0)}</span>
              </div>
              <span className="text-xs text-zinc-400 uppercase tracking-wider">Product Image</span>
            </div>
          )}
        </div>

        {/* Info column */}
        <div className="space-y-3">
          {/* Title */}
          <h1 className="text-xl leading-snug font-medium text-zinc-900">{product.name}</h1>

          {/* Rating row */}
          <div className="flex items-center gap-2">
            <div className="flex items-center">
              {Array.from({ length: 5 }).map((_, i) => {
                const filled = i < Math.floor(Number(stars));
                const half = !filled && i < Math.ceil(Number(stars));
                return (
                  <Star
                    key={i}
                    className={`h-3.5 w-3.5 ${
                      filled ? "text-amber-400 fill-amber-400" : half ? "text-amber-400 fill-amber-400/50" : "text-zinc-200"
                    }`}
                  />
                );
              })}
            </div>
            <span className="text-xs text-[#007185] hover:text-[#c7511f] hover:underline cursor-pointer">
              {reviewCount} ratings
            </span>
          </div>

          <div className="border-b border-zinc-200" />

          {/* Price */}
          <div className="space-y-1">
            <div className="flex items-baseline gap-1">
              <span className="text-xs text-zinc-500">$</span>
              <span className="text-3xl font-semibold tracking-tight text-zinc-900">
                {Number(product.price).toFixed(2).split(".")[0]}
              </span>
              <span className="text-sm text-zinc-500">
                .{Number(product.price).toFixed(2).split(".")[1]}
              </span>
            </div>
            <div className="text-xs text-zinc-600">
              <span className="font-medium text-green-700">FREE delivery</span>{" "}
              <span className="text-zinc-500">by tomorrow</span>
            </div>
          </div>

          <div className="border-b border-zinc-200" />

          {/* Description */}
          <p className="text-sm leading-6 text-zinc-700">
            {product.description ?? "No description available."}
          </p>

          {/* Stock status */}
          <div className="text-sm">
            {product.stock_quantity > 10 ? (
              <span className="text-green-700 font-medium">In Stock</span>
            ) : product.stock_quantity > 0 ? (
              <span className="text-amber-600 font-medium">Only {product.stock_quantity} left in stock - order soon</span>
            ) : (
              <span className="text-red-600 font-medium">Currently unavailable</span>
            )}
          </div>

          {/* Add to cart module */}
          {product.stock_quantity > 0 ? (
            <div className="rounded-sm border border-zinc-200 p-4 space-y-3">
              <div className="flex items-baseline gap-1">
                <span className="text-xs text-zinc-500">$</span>
                <span className="text-2xl font-semibold tracking-tight text-zinc-900">
                  {Number(product.price).toFixed(2).split(".")[0]}
                </span>
                <span className="text-xs text-zinc-500">
                  .{Number(product.price).toFixed(2).split(".")[1]}
                </span>
              </div>
              <AddToCartButton
                product={product}
                label="Add to Cart"
                className="w-full rounded-sm bg-[#ffd814] py-2 text-sm font-medium text-[#111] hover:bg-[#f7ca00] border-0 transition-colors"
              />
              <AddToCartButton
                product={product}
                label="Buy Now"
                className="w-full rounded-sm bg-[#fa8900] py-2 text-sm font-medium text-white hover:bg-[#e67e00] border-0 transition-colors"
              />
            </div>
          ) : null}
        </div>
      </div>

      {/* Related products */}
      {related.length > 0 ? (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold text-zinc-900">Related products</h2>
            <Link
              href="/products"
              className="text-xs font-medium text-[#007185] hover:text-[#c7511f] hover:underline"
            >
              See all &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {related.map((item) => (
              <ProductCard key={item.id} product={item} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
