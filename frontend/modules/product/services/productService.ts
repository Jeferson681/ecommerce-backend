import { apiFetch } from "@/core/http/apiFetch";
import type { Product, ProductPage } from "@/modules/product/types/product";

export type ProductListParams = {
  page?: number;
  per_page?: number;
  q?: string;
  category?: string;
  sort?: string;
};

export const productService = {
  list(): Promise<Product[]> {
    return apiFetch<Product[]>("/products");
  },

  listPage(params: ProductListParams): Promise<ProductPage> {
    const search = new URLSearchParams();
    if (params.page !== undefined) search.set("page", String(params.page));
    if (params.per_page !== undefined) search.set("per_page", String(params.per_page));
    if (params.q) search.set("q", params.q);
    if (params.category) search.set("category", params.category);
    if (params.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<ProductPage>(`/products${qs ? `?${qs}` : ""}`);
  },

  get(id: number): Promise<Product> {
    return apiFetch<Product>(`/products/${id}`);
  },

  create(data: Partial<Product>): Promise<Product> {
    return apiFetch<Product>("/products", {
      method: "POST",
      body: data,
    });
  },

  update(id: number, data: Partial<Product>): Promise<Product> {
    return apiFetch<Product>(`/products/${id}`, {
      method: "PATCH",
      body: data,
    });
  },

  delete(id: number): Promise<void> {
    return apiFetch<void>(`/products/${id}`, {
      method: "DELETE",
    });
  },
};
