import { apiFetch } from "@/core/http/apiFetch";
import type { Product } from "@/modules/product/types/product";

export const productService = {
  list(): Promise<Product[]> {
    return apiFetch<Product[]>("/products");
  },

  get(id: number): Promise<Product> {
    return apiFetch<Product>(`/products/${id}`);
  },
};
