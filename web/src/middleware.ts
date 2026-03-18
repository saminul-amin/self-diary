import { NextResponse, type NextRequest } from 'next/server';

/**
 * Route protection middleware.
 *
 * Since we use in-memory JWT tokens (not cookies), this middleware acts
 * as a lightweight guard. The client-side AuthProvider handles the real
 * auth state; this just ensures that basic route redirects work for
 * direct URL navigation.
 *
 * Protected routes: /entries, /tags, /search, /settings
 * Public routes: /login, /register
 */

const publicPaths = ['/login', '/register'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Let public routes and static assets pass through
  if (
    publicPaths.some((p) => pathname.startsWith(p)) ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname === '/'
  ) {
    return NextResponse.next();
  }

  // For protected routes, the actual auth check happens client-side.
  // We allow the request through — the AuthProvider will redirect
  // unauthenticated users to /login.
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
