import Image from "next/image"

import { cn } from "@/lib/utils"

/** The MyKhata mark: an open khata (ledger) with ₹ on one page and entries on the other. Same art as app/icon.svg.
 *  Rendered as an image so icon-size rules for inline SVGs (e.g. in the sidebar) never shrink it. */
export function LogoMark({ className, size = 40 }: { className?: string; size?: number }) {
  return (
    <Image src="/logo-mark.svg" alt="" width={size} height={size} unoptimized priority
      className={cn("shrink-0 select-none", className)} />
  )
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)} translate="no">
      <LogoMark size={36} className="size-9" />
      <span className="text-lg font-bold tracking-tight">
        My<span className="text-primary">Khata</span>
      </span>
    </span>
  )
}
