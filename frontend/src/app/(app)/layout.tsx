import type { ReactNode } from "react"

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { SessionProvider } from "@/features/auth/session-provider"
import { TransactionsProvider } from "@/features/transactions/transactions-provider"

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <TransactionsProvider>
        <SidebarProvider>
          <AppSidebar variant="inset" />
          <SidebarInset>
            <a
              href="#main"
              className="sr-only z-50 rounded-md bg-background px-3 py-2 text-sm font-medium shadow focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
            >
              Skip to content
            </a>
            <SiteHeader />
            <main id="main" tabIndex={-1} className="flex flex-1 flex-col gap-6 p-4 outline-none lg:p-6">
              {children}
            </main>
          </SidebarInset>
        </SidebarProvider>
      </TransactionsProvider>
    </SessionProvider>
  )
}
