"use client"

import { FileUp } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import { NAV } from "@/components/app-sidebar"
import { ModeToggle } from "@/components/mode-toggle"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"

const TITLES: Record<string, string> = Object.fromEntries(
  [...NAV.flatMap((g) => g.items), { href: "/settings", title: "Settings" }].map((i) => [i.href, i.title]),
)

export function SiteHeader() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 lg:px-6">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mx-1 data-[orientation=vertical]:h-4" />
      <h1 className="text-base font-medium text-balance">{TITLES[pathname] ?? "MyKhata"}</h1>
      <div className="ml-auto flex items-center gap-2">
        <Button variant="outline" size="sm" asChild className="hidden sm:inline-flex">
          <Link href="/statements">
            <FileUp aria-hidden /> Upload statement
          </Link>
        </Button>
        <ModeToggle />
      </div>
    </header>
  )
}
