import type { ReactNode } from "react"

import { Logo } from "@/components/logo"
import { ModeToggle } from "@/components/mode-toggle"

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col bg-muted/40">
      <header className="flex items-center justify-between px-4 py-3 sm:px-6">
        <Logo />
        <ModeToggle />
      </header>
      <main className="flex flex-1 items-center justify-center px-4 py-10">{children}</main>
    </div>
  )
}
