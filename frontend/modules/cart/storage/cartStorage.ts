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

/**
 * Push locally-only cart items (those without a server id) to the backend.
 * Handles the case where items were added before login or sync failed.
 * After sync, refreshes the local state from server to get assigned ids.
 */
async function syncLocalItemsToServer(): Promise<void> {
  if (globalThis.window === undefined) return;
  if (!tokenStorage.getAccessToken()) return;

  const items = readItems();

  // Only sync items that don't have a server id yet
  const unsyncedItems = items.filter((item) => item.id === null || item.cartId === null);

  if (unsyncedItems.length === 0) return;

  // Push each unsynced item to the server, one at a time.
  // Using individual POST /cart/items to match the existing API pattern.
  for (const item of unsyncedItems) {
    try {
      await addCartItem(item.productId, item.quantity);
    } catch {
      // If a single item fails, continue with others.
      // The server will reject duplicates or invalid products on its own.
      console.error("cartStorage: failed to sync item", item.productId);
    }
  }

  // Refresh from server to get the authoritative state with server ids
  await refreshFromServer();
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
    const previousItems = readItems();
    const nextItems = previousItems.map((item) =>
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
        .catch((err) => {
          console.error("cartStorage: failed to sync addItem to server", err);
          // Don't rollback — keep items locally so they can be retried later
        });
    }
  },

  updateQuantity(productId: number, quantity: number): void {
    const cachedItem = findCachedItemByProductId(productId);
    const previousItems = readItems();

    const nextItems = previousItems
      .map((item) =>
        getStoredProductId(item) === productId ? { ...normalizeItem(item), quantity } : item
      )
      .filter((item) => item.quantity > 0);

    writeItems(nextItems);

    if (globalThis.window !== undefined && tokenStorage.getAccessToken()) {
      if (cachedItem?.id) {
        if (quantity > 0) {
          void updateCartItem(cachedItem.id, quantity)
            .then(() => refreshFromServer())
            .catch((err) => {
              console.error("cartStorage: failed to sync updateQuantity to server", err);
              writeItems(previousItems);
            });
        } else {
          void removeCartItem(cachedItem.id)
            .then(() => refreshFromServer())
            .catch((err) => {
              console.error("cartStorage: failed to sync removeItem to server", err);
              writeItems(previousItems);
            });
        }
      } else {
        void refreshFromServer();
      }
    }
  },

  removeItem(productId: number): void {
    const cachedItem = findCachedItemByProductId(productId);
    const previousItems = readItems();

    const nextItems = previousItems.filter((item) => getStoredProductId(item) !== productId);
    writeItems(nextItems);

    if (globalThis.window !== undefined && tokenStorage.getAccessToken()) {
      if (cachedItem?.id) {
        void removeCartItem(cachedItem.id)
          .then(() => refreshFromServer())
          .catch((err) => {
            console.error("cartStorage: failed to sync removeItem to server", err);
            writeItems(previousItems);
          });
      } else {
        void refreshFromServer();
      }
    }
  },

  clear(): void {
    writeItems([]);
  },

  refresh(): void {
    syncFromServer();
  },

  /** Push local-only items to the server and refresh state.
   *  Must be called before checkout to ensure the server cart matches local state.
   */
  syncLocalBeforeCheckout(): Promise<void> {
    return syncLocalItemsToServer();
  },
};
