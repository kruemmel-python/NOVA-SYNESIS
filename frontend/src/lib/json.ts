export function safeJsonParse<T>(raw: string): T {
  return JSON.parse(raw) as T;
}

export function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
