import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// Where Supabase redirects the browser after the user clicks the magic
// link in their email. Exchanges the one-time code for a real session
// (stored in cookies by the server client), then sends them on to
// wherever they were headed — /dashboard by default.
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  const failureUrl = new URL("/login", origin);
  failureUrl.searchParams.set("error", "auth-callback-failed");
  return NextResponse.redirect(failureUrl);
}
