"use client";

import { useMemo, useSyncExternalStore } from "react";

import { cartStorage } from "@/modules/cart/storage/cartStorage";

const EMPTY_ITEMS: never[] = [];

export function useCart() {
  const items = useSyncExternalStore(cartStorage.subscribe, cartStorage.getSnapshot, () => EMPTY_ITEMS);

  return useMemo(() => {
    const itemCount = items.reduce((total, item) => total + item.quantity, 0);
    const subtotal = items.reduce((total, item) => {
      const price = Number(item.product.price);
      return total + (Number.isFinite(price) ? price * item.quantity : 0);
    }, 0);

    return {
      items,
      itemCount,
      subtotal,
      isEmpty: items.length === 0,
      addItem: cartStorage.addItem,
      updateQuantity: cartStorage.updateQuantity,
      removeItem: cartStorage.removeItem,
      clear: cartStorage.clear,
    };
  }, [items]);
}
