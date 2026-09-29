import Link from 'next/link'
import { Logo } from '@/components/brand/logo'
import { Button } from '@/components/ui/button'

const NAV = [
  { href: '/#how-it-works', label: 'How it works' },
  { href: '/#features', label: 'Features' },
  { href: '/#security', label: 'Security' },
  { href: '/#faq', label: 'FAQ' },
]

export function SiteHeader({ signedIn }: { signedIn: boolean }) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
        <Logo />
        <nav aria-label="Main" className="hidden items-center gap-6 md:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {signedIn ? (
            <Button render={<Link href="/dashboard" />} size="sm">
              Open dashboard
            </Button>
          ) : (
            <>
              <Button render={<Link href="/login" />} variant="ghost" size="sm">
                Log in
              </Button>
              <Button render={<Link href="/signup" />} size="sm">
                Start free
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
