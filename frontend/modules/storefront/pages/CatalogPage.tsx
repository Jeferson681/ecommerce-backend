import { PageHeader } from "@/shared/components/PageHeader";
import { SearchBar } from "@/shared/components/SearchBar";
import { ProductCard } from "@/modules/product/components/ProductCard";
import { productService } from "@/modules/product/services/productService";

type CatalogPageProps = {
  title?: string;
  description?: string;
  query?: string;
};

export default async function CatalogPage({
  title = "Catalog",
  description = "Browse the full collection",
  query,
}: CatalogPageProps) {
  let products: Awaited<ReturnType<typeof productService.list>> = [];
  let loadError: string | null = null;

  try {
    products = await productService.list();
  } catch (err) {
    products = [];
    loadError = err instanceof Error ? err.message : "Failed to load products";
  }
  const normalizedQuery = query?.trim().toLowerCase() ?? "";
  const filtered = products.filter((product) => {
    if (!product.is_active) return false;
    if (!normalizedQuery) return true;
    return [product.name, product.description ?? ""].join(" ").toLowerCase().includes(normalizedQuery);
  });

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-zinc-200 bg-white p-6 shadow-sm">
        <PageHeader title={title} description={description} />
        <SearchBar />
      </section>

      {loadError ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Catalog backend is unavailable right now. ({loadError})
        </div>
      ) : null}

      <div className="flex items-center justify-between gap-3 text-sm text-zinc-600">
        <div>{filtered.length} products found</div>
        {normalizedQuery ? <div>Showing results for &quot;{query}&quot;</div> : <div>All categories</div>}
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-sm text-zinc-600">
          No products matched your search.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
