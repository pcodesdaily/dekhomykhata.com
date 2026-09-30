// Readable payee from a bank narration, e.g. "UPI-BUNDL TECHNOLOGIES-swiggy@ybl-..." -> "Swiggy".
const LEGAL_NAMES: Record<string, string> = {
  "BUNDL TECHNOLOGIES": "Swiggy",
  "ANI TECHNOLOGIES": "Ola",
  "ETERNAL LIMITED": "Zomato",
  "KIRANAKART TECHNOLOGIES": "Zepto",
  "BLINK COMMERCE": "Blinkit",
  "AVENUE SUPERMARTS": "DMart",
  "FASHNEAR TECHNOLOGIES": "Meesho",
  "DREAMPLUG TECHNOLOGIES": "CRED",
  "CRED CLUB": "CRED",
  "NEXTBILLION TECHNOLOGY": "Groww",
  "BIGTREE ENTERTAINMENT": "BookMyShow",
  "INTERGLOBE AVIATION": "IndiGo",
  "ORAVEL STAYS": "OYO",
  "AMAZON PAY INDIA": "Amazon",
  "UBER INDIA SYSTEMS": "Uber",
  "MYNTRA DESIGNS": "Myntra",
}

const PATTERNS = [
  /^(?:REV-)?UPI-([^-]+)-/i,
  /^(?:TO TRANSFER-|BY TRANSFER-)?UPI\/(?:DR|CR)\/\d+\/([^/]+)\//i,
  /^UPI\/P2[MA]\/\d+\/([^/]+)\//i,
  /^ACH [DC]-\s*([^-]+)-/i,
  /^NEFT CR-[^-]+-([^-]+)-/i,
  /^ME DC SI \S+ (.+)$/i,
  /^POS \S+ (.+?)(?: [A-Z]{4,})?$/,
]

const SMALL = new Set(["and", "of", "the", "for"])

function titleCase(text: string): string {
  return text
    .toLowerCase()
    .split(/\s+/)
    .map((w, i) => (i > 0 && SMALL.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(" ")
}

export function payeeName(narration: string): string {
  const text = narration.trim()
  for (const pattern of PATTERNS) {
    const match = text.match(pattern)
    if (match?.[1]) {
      const raw = match[1].trim().toUpperCase()
      return LEGAL_NAMES[raw] ?? titleCase(raw)
    }
  }
  return text.length > 32 ? `${text.slice(0, 30)}…` : text
}
