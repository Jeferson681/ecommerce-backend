import CatalogPage from "@/modules/storefront/pages/CatalogPage";

type SearchPageProps = {
  query?: string;
};

export default async function SearchPage({ query }: SearchPageProps) {
  return <CatalogPage title="Search results" description="Find products by name or description" query={query} />;
}
