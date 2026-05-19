import type { Product } from "@/modules/product/types/product";

export type CartItem = {
  product: Product;
  quantity: number;
};
