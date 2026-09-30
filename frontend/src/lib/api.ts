export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

type Json = Record<string, unknown> | unknown[]

function messageFrom(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown })?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, "")
  if (status >= 500) return "Something went wrong on our side. Please try again."
  return "The request could not be completed."
}

export async function api<T>(path: string, options: { method?: string; json?: Json; body?: FormData } = {}): Promise<T> {
  const { method = "GET", json, body } = options
  const headers: Record<string, string> = { "x-mykhata-request": "1" }
  if (json) headers["content-type"] = "application/json"

  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: json ? JSON.stringify(json) : body,
      credentials: "same-origin",
    })
  } catch {
    throw new ApiError("Can't reach MyKhata. Check your connection and try again.", 0)
  }

  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined" && !location.pathname.startsWith("/login")) {
      // Full reload on purpose: drops any financial data still held in memory.
      const login = new URL("/login", location.origin)
      login.searchParams.set("next", location.pathname)
      window.location.replace(login.href)
    }
    throw new ApiError(messageFrom(data, response.status), response.status)
  }
  return data as T
}
