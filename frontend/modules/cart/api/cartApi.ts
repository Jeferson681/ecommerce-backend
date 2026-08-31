import { apiFetch } from "@/core/http/apiFetch";

export type CartItemResponse = {
  id: number;
  cart_id: number;
  product_id: number;
  quantity: number;
  created_at: string;
  updated_at: string;
};

export type CartResponse = {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
  items: CartItemResponse[];
};

export async function getCart(): Promise<CartResponse> {
  return apiFetch<CartResponse>("/cart");
}

export async function addCartItem(productId: number, quantity = 1): Promise<CartItemResponse> {
  return apiFetch<CartItemResponse>("/cart/items", {
    method: "POST",
    body: { product_id: productId, quantity },
  });
}

export async function updateCartItem(itemId: number, quantity: number): Promise<CartItemResponse> {
  return apiFetch<CartItemResponse>(`/cart/items/${itemId}`, {
    method: "PATCH",
    body: { quantity },
  });
}

export async function removeCartItem(itemId: number): Promise<void> {
  return apiFetch<void>(`/cart/items/${itemId}`, {
    method: "DELETE",
  });
}

export async function clearCart(): Promise<void> {
  return apiFetch<void>("/cart", {
    method: "DELETE",
  });
}
