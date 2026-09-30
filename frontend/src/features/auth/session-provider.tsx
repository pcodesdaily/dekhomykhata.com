"use client"

import { useRouter } from "next/navigation"
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { toast } from "sonner"

import { api } from "@/lib/api"

export interface User {
  id: number
  name: string
  email: string
  confidence_threshold: number
}

interface SessionValue {
  user: User | null
  setUser: (user: User) => void
  logout: () => Promise<void>
}

const SessionContext = createContext<SessionValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    api<User>("/auth/me").then(setUser).catch(() => undefined)
  }, [])

  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" })
    } finally {
      router.replace("/login")
      router.refresh()
      toast("Logged out")
    }
  }, [router])

  const value = useMemo(() => ({ user, setUser, logout }), [user, logout])
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) throw new Error("useSession must be used inside <SessionProvider>")
  return context
}
