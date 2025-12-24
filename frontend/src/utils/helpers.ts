import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// Parse a salary string and return detected currency symbol (if any) and the numeric/phrase part
export function parseSalary(input: string | undefined | null): {
  symbol: string | null;
  amount: string | null;
} {
  if (!input) return { symbol: null, amount: null };
  const s = input.trim();

  // Detect single-character currency symbol (Unicode currency symbols)
  const symbolMatch = s.match(/\p{Sc}/u);
  if (symbolMatch) {
    const symbol = symbolMatch[0];
    const amount = s.replace(/\p{Sc}/gu, "").trim();
    return { symbol, amount: amount || null };
  }

  // Detect common currency codes (USD, GBP, EUR, etc.) and map to symbols
  const codeMatch = s.match(/\b(USD|GBP|EUR|AUD|CAD|JPY|CHF|NZD)\b/i);
  const codeToSymbol: Record<string, string> = {
    USD: "$",
    GBP: "£",
    EUR: "€",
    AUD: "$",
    CAD: "$",
    JPY: "¥",
    CHF: "CHF",
    NZD: "$",
  };
  if (codeMatch) {
    const code = codeMatch[1].toUpperCase();
    const symbol = codeToSymbol[code] || code;
    const amount = s.replace(new RegExp(code, "gi"), "").trim();
    return { symbol, amount: amount || null };
  }

  // No explicit currency found — return amount as-is, symbol null
  return { symbol: null, amount: s || null };
}
