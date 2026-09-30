import { NextResponse, type NextRequest } from "next/server"

// Optimistic check only: the API verifies the session on every request.
const SESSION_COOKIE = "mykhata_session"
const AUTH_PAGES = ["/login"]

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl
  const signedIn = request.cookies.has(SESSION_COOKIE)
  const onAuthPage = AUTH_PAGES.includes(pathname)

  if (!signedIn && !onAuthPage) {
    const url = new URL("/login", request.url)
    if (pathname !== "/") url.searchParams.set("next", pathname + search)
    return NextResponse.redirect(url)
  }
  if (signedIn && onAuthPage) return NextResponse.redirect(new URL("/dashboard", request.url))
  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|ico|webp)$).*)"],
}
