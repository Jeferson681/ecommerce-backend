"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextQuery = query.trim();
    router.push(nextQuery ? `/search?q=${encodeURIComponent(nextQuery)}` : "/products");
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full items-center">
      <div className="relative flex-1">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search products..."
          className="h-9 w-full rounded-l-md border-0 bg-white px-3 pr-9 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 focus:ring-2 focus:ring-[#febd69]"
        />
      </div>
      <button
        type="submit"
        className="flex h-9 w-10 items-center justify-center rounded-r-md bg-[#febd69] text-[#131921] hover:bg-[#f3a847] transition-colors"
      >
        <Search className="h-4 w-4" />
      </button>
    </form>
  );
}
