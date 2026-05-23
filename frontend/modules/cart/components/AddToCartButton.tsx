"use client";

import { useState } from "react";

import type { Product } from "@/modules/product/types/product";
import { cartStorage } from "@/modules/cart/storage/cartStorage";

type AddToCartButtonProps = {
  product: Product;
  quantity?: number;
  className?: string;
  label?: string;
};

export function AddToCartButton({ product, quantity = 1, className, label = "Add to Cart" }: AddToCartButtonProps) {
  const [added, setAdded] = useState(false);

  return (
    <button
      className={className}
      onClick={() => {
        cartStorage.addItem(product, quantity);
        setAdded(true);
        window.setTimeout(() => setAdded(false), 1200);
      }}
    >
      {added ? "✓ Added" : label}
    </button>
  );
}
