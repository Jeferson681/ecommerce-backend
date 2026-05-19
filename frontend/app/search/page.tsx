import SearchPage from "@/modules/storefront/pages/SearchPage";

type PageProps = {
  searchParams?: Promise<{ q?: string }>;
};

export default async function Page({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  return <SearchPage query={params.q} />;
}
