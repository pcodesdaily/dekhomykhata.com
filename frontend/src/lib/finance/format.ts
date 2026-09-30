const rupees = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 })
const rupeesPrecise = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 })
const compact = new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 })

export function formatINR(amount: number, precise = false): string {
  return (precise ? rupeesPrecise : rupees).format(amount)
}

export function formatINRCompact(amount: number): string {
  return `₹${compact.format(amount)}`
}

export function formatPercent(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`
}

type DateStyle = Intl.DateTimeFormatOptions

const dateFormats = new Map<string, Intl.DateTimeFormat>()
const utc = (iso: string) => new Date(`${iso.slice(0, 10)}T00:00:00Z`)

function formatWith(date: Date, options: DateStyle): string {
  if (Number.isNaN(date.getTime())) return "—"
  const key = JSON.stringify(options)
  if (!dateFormats.has(key)) dateFormats.set(key, new Intl.DateTimeFormat("en-IN", { ...options, timeZone: "UTC" }))
  return dateFormats.get(key)!.format(date)
}

export function formatDate(iso: string, options: DateStyle = { day: "numeric", month: "short", year: "numeric" }): string {
  return formatWith(utc(iso), options)
}

export function formatMonth(key: string, options: DateStyle = { month: "short", year: "numeric" }): string {
  return formatWith(utc(`${key}-01`), options)
}
