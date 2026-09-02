import Link from "next/link";

import { productService } from "@/modules/product/services/productService";
import type { ProductPage } from "@/modules/product/types/product";
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

const PER_PAGE = 20;

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const categoryFilter = typeof params.category === "string" ? params.category : null;
  const priceFilter = typeof params.price === "string" ? params.price : null;
  const sortFilter = typeof params.sort === "string" ? params.sort : null;
  const rawPage = Array.isArray(params.page) ? params.page[0] : params.page;
  const parsedPage = Number.parseInt(rawPage ?? "1", 10);
  const currentPage = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;

  const priceRange = priceFilter ? parsePriceRange(priceFilter) : null;

  let productPage: ProductPage | null = null;
  let loadError = false;

  try {
    productPage = await productService.listPage({
      page: currentPage,
      per_page: PER_PAGE,
      // Sidebar slugs are search terms, not database category values: reuse the
      // same name/description matching the page used before, now server-side.
      q: categoryFilter ? categoryFilter.replace(/-/g, " ") : undefined,
      // Price range is applied server-side so `total`/`total_pages` and the
      // returned page slice stay consistent with the filter.
      min_price: priceRange?.[0],
      max_price: priceRange?.[1],
      sort: mapSortToApi(sortFilter),
    });
  } catch {
    productPage = null;
    loadError = true;
  }

  // `is_active` remains a client-side refinement: the catalog contract does
  // not expose an active filter.
  const activeProducts = (productPage?.items ?? []).filter((p) => p.is_active);

  const totalCount = productPage?.total ?? activeProducts.length;
  const totalPages = productPage?.total_pages ?? 1;

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
                  { label: "Newest", value: "newest" },
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

          {/* Pagination */}
          {totalPages > 1 ? (
            <nav className="mt-4 flex items-center justify-between border-t border-zinc-200 pt-3" aria-label="Pagination">
              {currentPage > 1 ? (
                <Link
                  href={buildPageUrl(categoryFilter, priceFilter, sortFilter, currentPage - 1)}
                  className="rounded-sm px-3 py-1.5 text-xs font-medium text-[#007185] hover:bg-zinc-100 hover:underline"
                >
                  &larr; Previous
                </Link>
              ) : (
                <span className="rounded-sm px-3 py-1.5 text-xs font-medium text-zinc-300">&larr; Previous</span>
              )}
              <span className="text-xs text-zinc-500">
                Page {currentPage} of {totalPages}
              </span>
              {currentPage < totalPages ? (
                <Link
                  href={buildPageUrl(categoryFilter, priceFilter, sortFilter, currentPage + 1)}
                  className="rounded-sm px-3 py-1.5 text-xs font-medium text-[#007185] hover:bg-zinc-100 hover:underline"
                >
                  Next &rarr;
                </Link>
              ) : (
                <span className="rounded-sm px-3 py-1.5 text-xs font-medium text-zinc-300">Next &rarr;</span>
              )}
            </nav>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function mapSortToApi(sort: string | null): "price_asc" | "price_desc" | "newest" | undefined {
  if (sort === "price-asc") return "price_asc";
  if (sort === "price-desc") return "price_desc";
  if (sort === "newest") return "newest";
  return undefined; // Featured -> backend default ordering
}

function buildPageUrl(category: string | null, price: string | null, sort: string | null, page: number): string {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (price) params.set("price", price);
  if (sort) params.set("sort", sort);
  if (page > 1) params.set("page", String(page));
  const qs = params.toString();
  return qs ? `/products?${qs}` : "/products";
}

function buildSortUrl(category: string | null, price: string | null, sort: string | null): string {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (price) params.set("price", price);
  if (sort) params.set("sort", sort);
  const qs = params.toString();
  return qs ? `/products?${qs}` : "/products";
}
