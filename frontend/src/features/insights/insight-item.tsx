import { Badge } from "@/components/ui/badge"
import type { Insight } from "@/lib/finance/types"
import { cn } from "@/lib/utils"

import { INSIGHT_KINDS } from "./insight-kinds"

export function InsightItem({ insight }: { insight: Insight }) {
  const kind = INSIGHT_KINDS[insight.kind]
  return (
    <li className="flex gap-3 py-3 first:pt-0 last:pb-0">
      <kind.icon className={cn("mt-0.5 size-4 shrink-0", kind.tone)} aria-hidden />
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">{insight.title}</span>
          <Badge variant="outline" className={cn("text-[11px]", kind.tone)}>
            {kind.label}
          </Badge>
        </div>
        <p className="text-sm break-words text-muted-foreground">{insight.detail}</p>
      </div>
    </li>
  )
}
