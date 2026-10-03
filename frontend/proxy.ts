import { NextResponse, type NextRequest } from 'next/server'
import { updateSession } from '@/lib/supabase/proxy'

export async function proxy(request: NextRequest) {
  const requestHost = request.headers.get('host')?.split(':', 1)[0].toLowerCase()
  if (requestHost === '0.0.0.0' || requestHost === '127.0.0.1') {
    const url = request.nextUrl.clone()
    url.hostname = 'localhost'
    return NextResponse.redirect(url)
  }
  return await updateSession(request)
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|api/backend|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
