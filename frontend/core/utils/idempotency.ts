/** Idempotency key generation for payment and checkout operations.
 *
 * Generates ONE key per logical attempt. On retry, the same key is reused
 * to avoid duplicate payment creation on the backend.
 */

function generateKey(): string {
  const bytes = new Uint8Array(32);
  globalThis.crypto.getRandomValues(bytes);
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return `ik-${hex}`;
}

export function createIdempotencyKey(): string {
  return generateKey();
}
