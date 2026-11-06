type QueryValue = string | number | null | undefined;

export function toSearchParams(values: Record<string, QueryValue>): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    const text = value === null || value === undefined ? '' : String(value).trim();
    if (text) {
      params.set(key, text);
    }
  }
  return params;
}
