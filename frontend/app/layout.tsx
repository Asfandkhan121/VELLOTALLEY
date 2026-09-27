import type { Metadata } from "next";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ledgerly — Bank statements to clean Excel",
  description:
    "Upload a bank statement PDF, review the extracted transactions, and download a formatted Excel workbook. Built for bookkeepers and small accounting firms.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col font-sans antialiased">
        <header className="border-b border-slate-200">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="font-serif text-lg font-semibold tracking-tight text-slate-900">
              Ledgerly
            </Link>
            <nav className="flex items-center gap-6 text-sm">
              <Link href="/privacy" className="text-slate-600 hover:text-slate-900">
                Privacy
              </Link>
              {session ? (
                <Link
                  href="/dashboard"
                  className="rounded-md bg-slate-900 px-3.5 py-1.5 font-medium text-white hover:bg-slate-800"
                >
                  Dashboard
                </Link>
              ) : (
                <Link
                  href="/login"
                  className="rounded-md bg-slate-900 px-3.5 py-1.5 font-medium text-white hover:bg-slate-800"
                >
                  Sign in
                </Link>
              )}
            </nav>
          </div>
        </header>
        <div className="flex-1">{children}</div>
        <footer className="border-t border-slate-200">
          <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <p>© {new Date().getFullYear()} Ledgerly.</p>
            <div className="flex gap-4">
              <Link href="/privacy" className="hover:text-slate-700">
                Privacy &amp; third-party AI use
              </Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
