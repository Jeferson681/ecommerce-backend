export function formatMoney(value: string | number, currency = "USD", locale = "en-US"): string {
  const numericValue = typeof value === "string" ? Number(value) : value;

  if (Number.isFinite(numericValue)) {
    return new Intl.NumberFormat(locale, { style: "currency", currency }).format(numericValue);
  }

  return String(value);
}
