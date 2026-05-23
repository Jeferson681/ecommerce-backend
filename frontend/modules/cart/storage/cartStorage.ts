import type { Product } from "@/modules/product/types/product";
import type { CartItem } from "@/modules/cart/types/cart";
import { tokenStorage } from "@/modules/auth/storage/tokenStorage";
import { productService } from "@/modules/product/services/productService";
import {
  addCartItem,
  getCart,
  removeCartItem,
  updateCartItem,
  type CartItemResponse,
} from "@/modules/cart/api/cartApi";

const CART_STORAGE_KEY = "cart_items";
const CART_EVENT = "cart_items_changed";

const EMPTY_ITEMS: CartItem[] = [];

type Listener = () => void;

let cachedRaw: string | null = null;
let cachedItems: CartItem[] = EMPTY_ITEMS;
let authSyncAttached = false;
let syncInFlight: Promise<void> | null = null;

function readItems(): CartItem[] {
  if (globalThis.window === undefined) return EMPTY_ITEMS;

  const raw = globalThis.window.localStorage.getItem(CART_STORAGE_KEY);
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
  if (globalThis.window === undefined) return;
  const raw = JSON.stringify(items);
  cachedRaw = raw;
  cachedItems = items.length > 0 ? items : EMPTY_ITEMS;
  globalThis.window.localStorage.setItem(CART_STORAGE_KEY, raw);
  globalThis.window.dispatchEvent(new Event(CART_EVENT));
}

function getStoredProductId(item: CartItem): number {
  return item.productId ?? item.product.id;
}

function normalizeItem(item: CartItem): CartItem {
  return {
    id: item.id ?? null,
    cartId: item.cartId ?? null,
    productId: item.productId ?? item.product.id,
    product: item.product,
    quantity: item.quantity,
    createdAt: item.createdAt,
    updatedAt: item.updatedAt,
  };
}

function toCartItem(product: Product, item: CartItemResponse): CartItem {
  return {
    id: item.id,
    cartId: item.cart_id,
    productId: item.product_id,
    product,
    quantity: item.quantity,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

async function resolveProductsById(productIds: number[]): Promise<Map<number, Product>> {
  const uniqueIds = [...new Set(productIds)];
  const products = await productService.list();
  const productMap = new Map(products.map((product) => [product.id, product]));

  for (const productId of uniqueIds) {
    if (productMap.has(productId)) continue;
    try {
      const product = await productService.get(productId);
      productMap.set(product.id, product);
    } catch {
      continue;
    }
  }

  return productMap;
}

async function refreshFromServer(): Promise<void> {
  if (globalThis.window === undefined) return;
  if (!tokenStorage.getAccessToken()) return;
  if (syncInFlight) return syncInFlight;

  syncInFlight = (async () => {
    try {
      const cart = await getCart();
      const productMap = await resolveProductsById(cart.items.map((item) => item.product_id));
      const nextItems: CartItem[] = cart.items
        .map((item) => {
          const product = productMap.get(item.product_id);
          if (!product) return null;
          return toCartItem(product, item);
        })
        .filter((item): item is CartItem => item !== null);

      writeItems(nextItems);
    } catch {
      return;
    } finally {
      syncInFlight = null;
    }
  })();

  return syncInFlight;
}

function syncFromServer(): void {
  void refreshFromServer();
}

function findCachedItemByProductId(productId: number): CartItem | undefined {
  return readItems().find((item) => getStoredProductId(item) === productId);
}

export const cartStorage = {
  getItems(): CartItem[] {
    return readItems();
  },

  getSnapshot(): CartItem[] {
    return readItems();
  },

  subscribe(listener: Listener): () => void {
    if (globalThis.window === undefined) return () => undefined;

    if (!authSyncAttached) {
      authSyncAttached = true;
      tokenStorage.subscribe(() => {
        if (tokenStorage.getAccessToken()) syncFromServer();
      });
      syncFromServer();
    }

    const onEvent = () => listener();
    globalThis.window.addEventListener(CART_EVENT, onEvent);
    globalThis.window.addEventListener("storage", onEvent);

    return () => {
      globalThis.window.removeEventListener(CART_EVENT, onEvent);
      globalThis.window.removeEventListener("storage", onEvent);
    };
  },

  setItems(items: CartItem[]): void {
    writeItems(items.map(normalizeItem));
  },

  addItem(product: Product, quantity = 1): void {
    const items = readItems();
    const nextItems = items.map((item) =>
      getStoredProductId(item) === product.id
        ? { ...normalizeItem(item), product, productId: product.id, quantity: item.quantity + quantity }
        : item
    );

    if (!nextItems.some((item) => getStoredProductId(item) === product.id)) {
      nextItems.push({
        id: null,
        cartId: null,
        productId: product.id,
        product,
        quantity,
      });
    }

    writeItems(nextItems);

    if (globalThis.window !== undefined && tokenStorage.getAccessToken()) {
      void addCartItem(product.id, quantity)
        .then(() => refreshFromServer())
        .catch(() => undefined);
    }
  },

  updateQuantity(productId: number, quantity: number): void {
    const nextItems = readItems()
      .map((item) =>
        getStoredProductId(item) === productId ? { ...normalizeItem(item), quantity } : item
      )
      .filter((item) => item.quantity > 0);

    writeItems(nextItems);

    if (globalThis.window !== undefined && tokenStorage.getAccessToken()) {
      const cachedItem = findCachedItemByProductId(productId);
      if (cachedItem?.id) {
        if (quantity > 0) {
          void updateCartItem(cachedItem.id, quantity)
            .then(() => refreshFromServer())
            .catch(() => undefined);
        } else {
          void removeCartItem(cachedItem.id)
            .then(() => refreshFromServer())
            .catch(() => undefined);
        }
      } else {
        void refreshFromServer();
      }
    }
  },

  removeItem(productId: number): void {
    const nextItems = readItems().filter((item) => getStoredProductId(item) !== productId);
    writeItems(nextItems);

    if (globalThis.window !== undefined && tokenStorage.getAccessToken()) {
      const cachedItem = findCachedItemByProductId(productId);
      if (cachedItem?.id) {
        void removeCartItem(cachedItem.id)
          .then(() => refreshFromServer())
          .catch(() => undefined);
      } else {
        void refreshFromServer();
      }
    }
  },

  clear(): void {
    writeItems([]);

    if (globalThis.window !== undefined && tokenStorage.getAccessToken()) {
      void (async () => {
        try {
          const cart = await getCart();
          await Promise.all(cart.items.map((item) => removeCartItem(item.id)));
        } catch {
          return;
        } finally {
          await refreshFromServer();
        }
      })();
    }
  },

  refresh(): void {
    syncFromServer();
  },
};
