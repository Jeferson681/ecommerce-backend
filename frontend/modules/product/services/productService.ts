import { apiFetch } from "@/core/http/apiFetch";
import type { Product } from "@/modules/product/types/product";

export const productService = {
  list(): Promise<Product[]> {
    return apiFetch<Product[]>("/products");
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
