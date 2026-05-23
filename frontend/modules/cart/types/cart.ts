import type { Product } from "@/modules/product/types/product";

export type CartItem = {
  id: number | null;
  cartId: number | null;
  productId: number;
  product: Product;
  quantity: number;
  createdAt?: string;
  updatedAt?: string;
};
