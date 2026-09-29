import { NextResponse, type NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'
export const maxDuration = 300

const SEGMENT_PATTERN = /^[A-Za-z0-9_-]+$/
const PASSTHROUGH_RESPONSE_HEADERS = ['content-type', 'content-disposition', 'content-length']

type RouteContext = { params: Promise<{ path: string[] }> }

function errorResponse(status: number, detail: string) {
  return NextResponse.json({ detail }, { status })
}

async function forward(request: NextRequest, context: RouteContext) {
  const baseUrl = process.env.BACKEND_API_URL
  if (!baseUrl) {
    return errorResponse(
      503,
      'The conversion service is not configured yet. Set BACKEND_API_URL to your FastAPI backend URL.',
    )
  }

  const { path } = await context.params
  if (path[0] !== 'v1' || !path.every((segment) => SEGMENT_PATTERN.test(segment))) {
    return errorResponse(404, 'Not found.')
  }

  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) {
    return errorResponse(401, 'Your session has expired. Please sign in again.')
  }
  const {
    data: { session },
  } = await supabase.auth.getSession()
  if (!session?.access_token) {
    return errorResponse(401, 'Your session has expired. Please sign in again.')
  }

  const target = new URL(path.join('/'), baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`)
  target.search = request.nextUrl.search

  const headers = new Headers({
    Authorization: `Bearer ${session.access_token}`,
    Accept: request.headers.get('accept') ?? '*/*',
  })
  const contentType = request.headers.get('content-type')
  if (contentType) headers.set('Content-Type', contentType)

  const hasBody = request.method !== 'GET' && request.method !== 'HEAD'

  let upstream: Response
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: 'no-store',
      redirect: 'manual',
    })
  } catch {
    return errorResponse(502, 'Could not reach the conversion service. Please try again shortly.')
  }

  const responseHeaders = new Headers({ 'Cache-Control': 'no-store' })
  for (const name of PASSTHROUGH_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name)
    if (value) responseHeaders.set(name, value)
  }

  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders })
}

export { forward as GET, forward as POST }
