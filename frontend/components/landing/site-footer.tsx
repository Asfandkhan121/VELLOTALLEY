import Link from 'next/link'
import { Logo } from '@/components/brand/logo'

export function SiteFooter() {
  return (
    <footer>
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 sm:px-6 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-2">
          <Logo />
          <p className="text-sm text-muted-foreground">Bank statements into structured accounting data.</p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <Link href="/#workflow" className="hover:text-foreground">Our roadmap</Link>
          <Link href="/#features" className="hover:text-foreground">Features</Link>
          <Link href="/#security" className="hover:text-foreground">Security</Link>
          <Link href="/privacy" className="hover:text-foreground">Privacy</Link>
          <Link href="/login" className="hover:text-foreground">Log in</Link>
        </nav>
      </div>
      <div className="border-t">
        <p className="mx-auto max-w-6xl px-4 py-4 text-xs text-muted-foreground sm:px-6">
          {`© ${new Date().getFullYear()} Vellotalley. All rights reserved.`}
        </p>
      </div>
    </footer>
  )
}
