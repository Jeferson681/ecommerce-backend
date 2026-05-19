import type { Product } from "@/modules/product/types/product";
import type { CartItem } from "@/modules/cart/types/cart";

const CART_STORAGE_KEY = "cart_items";
const CART_EVENT = "cart_items_changed";

const EMPTY_ITEMS: CartItem[] = [];

type Listener = () => void;

let cachedRaw: string | null = null;
let cachedItems: CartItem[] = EMPTY_ITEMS;

function readItems(): CartItem[] {
  if (typeof window === "undefined") return EMPTY_ITEMS;

  const raw = window.localStorage.getItem(CART_STORAGE_KEY);
  if (!raw) {
    if (cachedRaw === null) return cachedItems;
    cachedRaw = null;
    cachedItems = EMPTY_ITEMS;
    return cachedItems;
  }

  if (raw === cachedRaw) return cachedItems;

  try {
    const parsed = JSON.parse(raw) as CartItem[];
    cachedRaw = raw;
    cachedItems = Array.isArray(parsed) ? parsed : [];
    return cachedItems;
  } catch {
    cachedRaw = raw;
    cachedItems = EMPTY_ITEMS;
    return cachedItems;
  }
}

function writeItems(items: CartItem[]): void {
  if (typeof window === "undefined") return;
  const raw = JSON.stringify(items);
  cachedRaw = raw;
  cachedItems = items.length > 0 ? items : EMPTY_ITEMS;
  window.localStorage.setItem(CART_STORAGE_KEY, raw);
  window.dispatchEvent(new Event(CART_EVENT));
}

export const cartStorage = {
  getItems(): CartItem[] {
    return readItems();
  },

  getSnapshot(): CartItem[] {
    return readItems();
  },

  subscribe(listener: Listener): () => void {
    if (typeof window === "undefined") return () => undefined;

    const onEvent = () => listener();
    window.addEventListener(CART_EVENT, onEvent);
    window.addEventListener("storage", onEvent);

    return () => {
      window.removeEventListener(CART_EVENT, onEvent);
      window.removeEventListener("storage", onEvent);
    };
  },

  setItems(items: CartItem[]): void {
    writeItems(items);
  },

  addItem(product: Product, quantity = 1): void {
    const items = readItems();
    const nextItems = items.map((item) =>
      item.product.id === product.id
        ? { ...item, product, quantity: item.quantity + quantity }
        : item
    );

    if (!nextItems.some((item) => item.product.id === product.id)) {
      nextItems.push({ product, quantity });
    }

    writeItems(nextItems);
  },

  updateQuantity(productId: number, quantity: number): void {
    const nextItems = readItems()
      .map((item) =>
        item.product.id === productId ? { ...item, quantity } : item
      )
      .filter((item) => item.quantity > 0);

    writeItems(nextItems);
  },

  removeItem(productId: number): void {
    const nextItems = readItems().filter((item) => item.product.id !== productId);
    writeItems(nextItems);
  },

  clear(): void {
    writeItems([]);
  },
};
