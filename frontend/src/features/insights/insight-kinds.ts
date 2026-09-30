import { AlertTriangle, Copy, PiggyBank, TrendingDown, TrendingUp, Zap, type LucideIcon } from "lucide-react"

import type { InsightKind } from "@/lib/finance/types"

export type InsightGroup = "alert" | "trend" | "saving"

export const INSIGHT_KINDS: Record<InsightKind, { label: string; icon: LucideIcon; tone: string; group: InsightGroup }> = {
  double_charge: { label: "Check", icon: Copy, tone: "text-red-700 dark:text-red-400", group: "alert" },
  unusual: { label: "Unusual", icon: Zap, tone: "text-amber-700 dark:text-amber-400", group: "alert" },
  price_change: { label: "Price change", icon: AlertTriangle, tone: "text-amber-700 dark:text-amber-400", group: "alert" },
  overspend: { label: "Overspent", icon: TrendingUp, tone: "text-red-700 dark:text-red-400", group: "trend" },
  underspend: { label: "Under budget", icon: TrendingDown, tone: "text-emerald-700 dark:text-emerald-400", group: "trend" },
  savings: { label: "Savings", icon: PiggyBank, tone: "text-amber-700 dark:text-amber-400", group: "saving" },
}
