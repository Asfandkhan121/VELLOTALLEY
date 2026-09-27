import { createBrowserClient } from "@supabase/ssr";

/** Browser-side Supabase client. Used wherever a client component needs the
 * current session — including lib/api.ts, which reads the access token off
 * it to authenticate every backend call. */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
