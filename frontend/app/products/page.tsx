import Link from "next/link";

import { productService } from "@/modules/product/services/productService";
import { ProductCard } from "@/modules/product/components/ProductCard";


function parsePriceRange(value: string): [number, number] | null {
  const parts = value.split("-");
  if (parts.length === 2) {
    const min = Number(parts[0]);
    const max = Number(parts[1]);
    if (Number.isFinite(min) && Number.isFinite(max)) return [min, max];
  }
  return null;
}

const categories = [
  { label: "Electronics", slug: "electronics" },
  { label: "Clothing", slug: "clothing" },
  { label: "Home & Kitchen", slug: "home-kitchen" },
  { label: "Sports", slug: "sports" },
  { label: "Books", slug: "books" },
  { label: "Toys & Games", slug: "toys" },
  { label: "Automotive", slug: "automotive" },
  { label: "Beauty", slug: "beauty" },
  { label: "Tools", slug: "tools" },
  { label: "Pet Supplies", slug: "pets" },
];

const priceRanges = [
  { label: "Under $25", value: "0-25" },
  { label: "$25 to $50", value: "25-50" },
  { label: "$50 to $100", value: "50-100" },
  { label: "$100 to $200", value: "100-200" },
  { label: "$200 & above", value: "200-999999" },
];

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const categoryFilter = typeof params.category === "string" ? params.category : null;
  const priceFilter = typeof params.price === "string" ? params.price : null;
  const sortFilter = typeof params.sort === "string" ? params.sort : null;

  let products: Awaited<ReturnType<typeof productService.list>> = [];
  let loadError = false;

  try {
    products = await productService.list();
  } catch {
    products = [];
    loadError = true;
  }

  let activeProducts = products.filter((p) => p.is_active);

  // Category filter
  if (categoryFilter) {
    activeProducts = activeProducts.filter(
      (p) => p.name.toLowerCase().includes(categoryFilter.replace("-", " ")) || (p.description ?? "").toLowerCase().includes(categoryFilter.replace("-", " "))
    );
  }

  // Price filter
  if (priceFilter) {
    const range = parsePriceRange(priceFilter);
    if (range) {
      const [min, max] = range;
      activeProducts = activeProducts.filter((p) => {
        const price = Number(p.price);
        return price >= min && price <= max;
      });
    }
  }

  // Sort
  if (sortFilter === "price-asc") {
    activeProducts.sort((a, b) => Number(a.price) - Number(b.price));
  } else if (sortFilter === "price-desc") {
    activeProducts.sort((a, b) => Number(b.price) - Number(a.price));
  } else if (sortFilter === "name") {
    activeProducts.sort((a, b) => a.name.localeCompare(b.name));
  } else if (sortFilter === "stock") {
    activeProducts.sort((a, b) => b.stock_quantity - a.stock_quantity);
  }

  const totalCount = activeProducts.length;

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-zinc-500" aria-label="Breadcrumb">
        <Link href="/" className="hover:text-zinc-800 transition-colors">
          Home
        </Link>
        <span className="text-zinc-300 mx-0.5">›</span>
        <span className="text-zinc-800 font-medium">All Products</span>
      </nav>

      {loadError ? (
        <div className="rounded-sm border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800">
          Products are unavailable right now. Please try again in a few minutes.
        </div>
      ) : null}

      <div className="flex gap-6">
        {/* Sidebar Filters */}
        <aside className="hidden w-56 shrink-0 lg:block">
          <div className="sticky top-[104px] space-y-5">
            {/* Categories */}
            <div>
              <h3 className="mb-2 text-sm font-bold text-zinc-900">Category</h3>
              <ul className="space-y-1">
                <li>
                  <Link
                    href="/products"
                    className={`block text-xs py-1 transition-colors ${
                      !categoryFilter ? "text-[#c7511f] font-semibold" : "text-zinc-600 hover:text-zinc-900"
                    }`}
                  >
                    All Categories
                  </Link>
                </li>
                {categories.map((cat) => (
                  <li key={cat.slug}>
                    <Link
                      href={categoryFilter === cat.slug ? "/products" : `/products?category=${cat.slug}`}
                      className={`block text-xs py-1 transition-colors ${
                        categoryFilter === cat.slug ? "text-[#c7511f] font-semibold" : "text-zinc-600 hover:text-zinc-900"
                      }`}
                    >
                      {cat.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Price Range */}
            <div>
              <h3 className="mb-2 text-sm font-bold text-zinc-900">Price</h3>
              <ul className="space-y-1">
                <li>
                  <Link
                    href={categoryFilter ? `/products?category=${categoryFilter}` : "/products"}
                    className={`block text-xs py-1 transition-colors ${
                      !priceFilter ? "text-[#c7511f] font-semibold" : "text-zinc-600 hover:text-zinc-900"
                    }`}
                  >
                    All Prices
                  </Link>
                </li>
                {priceRanges.map((range) => {
                  const href = categoryFilter
                    ? `/products?category=${categoryFilter}&price=${range.value}`
                    : `/products?price=${range.value}`;
                  return (
                    <li key={range.value}>
                      <Link
                        href={priceFilter === range.value ? (categoryFilter ? `/products?category=${categoryFilter}` : "/products") : href}
                        className={`block text-xs py-1 transition-colors ${
                          priceFilter === range.value ? "text-[#c7511f] font-semibold" : "text-zinc-600 hover:text-zinc-900"
                        }`}
                      >
                        {range.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* Active filter indicator */}
            {categoryFilter || priceFilter || sortFilter ? (
              <Link
                href="/products"
                className="block text-xs font-medium text-[#007185] hover:text-[#c7511f] hover:underline"
              >
                Clear all filters
              </Link>
            ) : null}
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          {/* Results header */}
          <div className="mb-3 flex items-center justify-between border-b border-zinc-200 pb-3">
            <div>
              <h1 className="text-base font-bold text-zinc-900">All Products</h1>
              <p className="text-xs text-zinc-500 mt-0.5">{totalCount} result{totalCount !== 1 ? "s" : ""}</p>
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500 hidden sm:inline">Sort by:</span>
              <div className="flex gap-1 text-xs">
                {[
                  { label: "Featured", value: null },
                  { label: "Price: Low", value: "price-asc" },
                  { label: "Price: High", value: "price-desc" },
                  { label: "Name", value: "name" },
                ].map((option) => {
                  const isActive = sortFilter === option.value || (!sortFilter && option.value === null);
                  const href = buildSortUrl(categoryFilter, priceFilter, option.value);
                  return (
                    <Link
                      key={option.label}
                      href={href}
                      className={`px-2 py-1 rounded-sm transition-colors ${
                        isActive
                          ? "bg-[#131921] text-white font-medium"
                          : "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100"
                      }`}
                    >
                      {option.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Mobile category filter bar */}
          <div className="mb-3 flex gap-1 overflow-x-auto pb-1 lg:hidden">
            <Link
              href="/products"
              className={`shrink-0 rounded-sm px-2.5 py-1 text-xs font-medium transition-colors ${
                !categoryFilter ? "bg-[#131921] text-white" : "bg-white border border-zinc-200 text-zinc-700 hover:border-zinc-300"
              }`}
            >
              All
            </Link>
            {categories.map((cat) => (
              <Link
                key={cat.slug}
                href={categoryFilter === cat.slug ? "/products" : `/products?category=${cat.slug}`}
                className={`shrink-0 rounded-sm px-2.5 py-1 text-xs font-medium transition-colors ${
                  categoryFilter === cat.slug ? "bg-[#131921] text-white" : "bg-white border border-zinc-200 text-zinc-700 hover:border-zinc-300"
                }`}
              >
                {cat.label}
              </Link>
            ))}
          </div>

          {/* Products Grid */}
          {activeProducts.length === 0 ? (
            <div className="rounded-sm border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500">
              No products match your filters.
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-5">
              {activeProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function buildSortUrl(category: string | null, price: string | null, sort: string | null): string {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (price) params.set("price", price);
  if (sort) params.set("sort", sort);
  const qs = params.toString();
  return qs ? `/products?${qs}` : "/products";
}
