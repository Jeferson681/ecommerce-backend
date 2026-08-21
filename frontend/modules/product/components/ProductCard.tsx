import Link from "next/link";
import { Star } from "lucide-react";

import type { Product } from "@/modules/product/types/product";
import { formatMoney } from "@/core/utils/money";
import { AddToCartButton } from "@/modules/cart/components/AddToCartButton";

type ProductCardProps = {
  product: Product;
};

export function ProductCard({ product }: ProductCardProps) {
  // Deterministic "random" values based on product id for SSR purity
  const seed = product.id;
  const hasDiscount = (seed * 7 + 3) % 10 > 6;
  const discountPercent = hasDiscount ? ((seed * 13 + 7) % 30) + 10 : 0;
  const originalPrice = hasDiscount ? Number(product.price) * (1 + discountPercent / 100) : null;
  const stars = (3.5 + ((seed * 17) % 15) / 10).toFixed(1);
  const reviewCount = ((seed * 31 + 5) % 500) + 10;

  return (
    <div className="group flex flex-col bg-white rounded-sm border border-zinc-200/80 hover:border-zinc-300 hover:shadow-md transition-all">
      {/* Product Image Area */}
      <Link
        href={`/products/${product.id}`}
        className="relative flex aspect-square items-center justify-center bg-white p-6 overflow-hidden"
      >
        {/* Product image or fallback placeholder */}
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.name}
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center rounded-sm bg-gradient-to-br from-zinc-50 to-zinc-100">
            <div className="text-center">
              <div className="mx-auto mb-2 h-16 w-16 rounded-full bg-zinc-200 flex items-center justify-center">
                <span className="text-2xl font-bold text-zinc-400">
                  {product.name.charAt(0)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Discount badge */}
        {hasDiscount ? (
          <span className="discount-badge absolute left-2 top-2">
            -{discountPercent}%
          </span>
        ) : null}
      </Link>

      {/* Product Info */}
      <div className="flex flex-1 flex-col gap-1.5 p-3">
        {/* Rating Row */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center">
            {Array.from({ length: 5 }).map((_, i) => {
              const filled = i < Math.floor(Number(stars));
              const half = !filled && i < Math.ceil(Number(stars));
              return (
                <Star
                  key={i}
                  className={`h-3 w-3 ${
                    filled ? "text-amber-400 fill-amber-400" : half ? "text-amber-400 fill-amber-400/50" : "text-zinc-200"
                  }`}
                />
              );
            })}
          </div>
          <span className="text-[11px] text-[#007185] hover:text-[#c7511f] hover:underline cursor-pointer">
            {reviewCount}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-sm leading-snug text-zinc-800 line-clamp-2">
          <Link
            href={`/products/${product.id}`}
            className="hover:text-[#c7511f] transition-colors"
          >
            {product.name}
          </Link>
        </h3>

        {/* Price Section */}
        <div className="mt-auto space-y-0.5">
          {originalPrice ? (
            <div className="text-xs text-zinc-500 line-through">
              {formatMoney(String(originalPrice))}
            </div>
          ) : null}

          <div className="flex items-baseline gap-1">
            <span className="text-xs text-zinc-500">$</span>
            <span className="text-xl font-semibold tracking-tight text-zinc-900">
              {Number(product.price).toFixed(2).split(".")[0]}
            </span>
            <span className="text-xs text-zinc-500">
              .{Number(product.price).toFixed(2).split(".")[1]}
            </span>
          </div>

          {/* Installments */}
          <div className="text-xs text-zinc-600">
            <span className="font-medium text-zinc-800">
              ${(Number(product.price) / 12).toFixed(2)}
            </span>
            <span className="text-zinc-500"> /month</span>
          </div>

          {/* Free shipping badge */}
          {Number(product.price) > 35 ? (
            <div className="text-xs text-green-700 font-medium">
              FREE delivery
            </div>
          ) : null}
        </div>

        {/* Stock indicator */}
        <div className="mt-1 text-[11px] text-zinc-500">
          {product.stock_quantity > 10 ? (
            <span className="text-green-700 font-medium">In Stock</span>
          ) : product.stock_quantity > 0 ? (
            <span className="text-amber-600 font-medium">
              Only {product.stock_quantity} left in stock
            </span>
          ) : (
            <span className="text-red-600 font-medium">Out of stock</span>
          )}
        </div>

        {/* Add to Cart */}
        {product.stock_quantity > 0 ? (
          <AddToCartButton
            product={product}
            label="Add to Cart"
            className="mt-1 w-full rounded-sm bg-[#ffd814] px-3 py-1.5 text-xs font-medium text-[#111] hover:bg-[#f7ca00] border-0 transition-colors"
          />
        ) : null}
      </div>
    </div>
  );
}
