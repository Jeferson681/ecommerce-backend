import { ProductCard } from "@/modules/product/components/ProductCard";
import { productService } from "@/modules/product/services/productService";
import { getUserErrorMessage } from "@/core/exceptions/userMessage";

type CatalogPageProps = {
  title?: string;
  description?: string;
  query?: string;
};

export default async function CatalogPage({
  title = "Search Results",
  query,
}: CatalogPageProps) {
  let products: Awaited<ReturnType<typeof productService.list>> = [];
  let loadError: string | null = null;

  try {
    products = await productService.list();
  } catch (err) {
    products = [];
    loadError = getUserErrorMessage(err);
  }
  const normalizedQuery = query?.trim().toLowerCase() ?? "";
  const filtered = products.filter((product) => {
    if (!product.is_active) return false;
    if (!normalizedQuery) return true;
    return [product.name, product.description ?? ""].join(" ").toLowerCase().includes(normalizedQuery);
  });

  return (
    <div className="space-y-4">
      {loadError ? (
        <div className="rounded-sm border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900">
          Catalog backend is unavailable right now. ({loadError})
        </div>
      ) : null}

      {/* Results header */}
      <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
        <div>
          <h1 className="text-base font-bold text-zinc-900">{title}</h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
            {normalizedQuery ? <> for &ldquo;{query}&rdquo;</> : null}
          </p>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-sm border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500">
          {normalizedQuery
            ? `No products matched "${query}". Try a different search.`
            : "No products available yet."}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {filtered.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
