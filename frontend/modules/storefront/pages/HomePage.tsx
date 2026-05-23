import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { productService } from "@/modules/product/services/productService";
import { ProductCard } from "@/modules/product/components/ProductCard";

export default async function HomePage() {
  let products: Awaited<ReturnType<typeof productService.list>> = [];
  try {
    products = await productService.list();
  } catch {
    products = [];
  }

  const activeProducts = products.filter((p) => p.is_active);
  const featured = activeProducts.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Deal of the day banner - compact */}
      <div className="bg-gradient-to-r from-[#131921] to-[#232f3e] rounded-sm px-5 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">{"Today's Deals"}</h2>
            <p className="text-sm text-[#febd69]">Free shipping on all items</p>
          </div>
          <Link
            href="/products"
            className="flex items-center gap-1 rounded-sm bg-[#febd69] px-4 py-1.5 text-xs font-bold text-[#131921] hover:bg-[#f3a847] transition-colors"
          >
            Shop now <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Main product grid - marketplace style */}
      {featured.length === 0 ? (
        <div className="rounded-sm border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500">
          No products available yet. Check back later.
        </div>
      ) : (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold text-zinc-900">Featured Products</h2>
            <Link
              href="/products"
              className="text-xs font-medium text-[#007185] hover:text-[#c7511f] hover:underline"
            >
              See all &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
            {featured.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}

      {/* Secondary products row */}
      {activeProducts.length > 8 ? (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold text-zinc-900">Best Sellers</h2>
            <Link
              href="/products"
              className="text-xs font-medium text-[#007185] hover:text-[#c7511f] hover:underline"
            >
              See all &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
            {activeProducts.slice(4, 16).map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Category quick links */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {["Electronics", "Clothing", "Home & Kitchen", "Sports"].map((cat) => (
          <Link
            key={cat}
            href={`/products?category=${cat.toLowerCase().replace(/ & /g, "-").replace(/ /g, "-")}`}
            className="rounded-sm border border-zinc-200 bg-white px-4 py-3 text-center text-xs font-medium text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50 hover:text-[#c7511f] transition-all"
          >
            {cat}
          </Link>
        ))}
      </section>
    </div>
  );
}
