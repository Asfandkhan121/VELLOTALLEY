"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

export function LoginForm({ next }: { next?: string }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setStatus("sending");
    setErrorMessage(null);

    const supabase = createClient();
    const redirectPath = next ? `/auth/callback?next=${encodeURIComponent(next)}` : "/auth/callback";
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}${redirectPath}` },
    });

    if (error) {
      setStatus("error");
      setErrorMessage(error.message);
      return;
    }
    setStatus("sent");
  }

  if (status === "sent") {
    return (
      <div className="mt-8 rounded-md border border-ledger-100 bg-ledger-50 px-4 py-4 text-sm text-ledger-700">
        Check <span className="font-medium">{email}</span> for a sign-in link.
        It&apos;ll bring you straight back here, signed in.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-3">
      <label htmlFor="email" className="block text-sm font-medium text-slate-700">
        Email address
      </label>
      <input
        id="email"
        name="email"
        type="email"
        required
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@firm.com"
        className="w-full rounded-md border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-ledger-600"
      />
      {status === "error" && errorMessage ? (
        <p className="text-sm text-red-700">{errorMessage}</p>
      ) : null}
      <button
        type="submit"
        disabled={status === "sending"}
        className="w-full rounded-md bg-ledger-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-ledger-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "sending" ? "Sending link…" : "Send sign-in link"}
      </button>
    </form>
  );
}
