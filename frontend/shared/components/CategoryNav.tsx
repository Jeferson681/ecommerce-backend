import Link from "next/link";

const categories = [
  { label: "Electronics", href: "/products?category=electronics" },
  { label: "Clothing", href: "/products?category=clothing" },
  { label: "Home & Kitchen", href: "/products?category=home-kitchen" },
  { label: "Sports", href: "/products?category=sports" },
  { label: "Books", href: "/products?category=books" },
  { label: "Toys & Games", href: "/products?category=toys" },
  { label: "Automotive", href: "/products?category=automotive" },
  { label: "Beauty", href: "/products?category=beauty" },
  { label: "Tools", href: "/products?category=tools" },
  { label: "Pet Supplies", href: "/products?category=pets" },
];

export function CategoryNav() {
  return (
    <nav className="sticky top-[52px] z-40 border-b border-zinc-300/70 bg-[#232f3e] text-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center gap-0 overflow-x-auto px-4">
        <Link
          href="/products"
          className="flex shrink-0 items-center gap-1 border-b-2 border-transparent px-3 py-2 text-[13px] font-medium hover:border-[#febd69] hover:bg-white/10 transition-colors"
        >
          <span className="text-base leading-none">☰</span>
          <span>All</span>
        </Link>
        {categories.slice(0, 7).map((cat) => (
          <Link
            key={cat.href}
            href={cat.href}
            className="whitespace-nowrap border-b-2 border-transparent px-3 py-2 text-[13px] font-medium text-zinc-200 hover:border-[#febd69] hover:text-white hover:bg-white/10 transition-colors"
          >
            {cat.label}
          </Link>
        ))}
        <span className="ml-auto shrink-0 px-3 text-[11px] text-zinc-400">|</span>
        <span className="shrink-0 px-3 text-[13px] font-medium text-[#febd69]">
          Lowest Prices
        </span>
      </div>
    </nav>
  );
}
