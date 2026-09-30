import Link from 'next/link'
import { cn } from '@/lib/utils'

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      aria-hidden="true"
      className={cn('size-7 shrink-0', className)}
      fill="none"
    >
      <rect width="32" height="32" rx="8" className="fill-primary" />
      <path
        d="M10 8.5h8.5l3.5 3.5v11.5a1 1 0 0 1-1 1H10a1 1 0 0 1-1-1v-14a1 1 0 0 1 1-1Z"
        className="stroke-primary-foreground"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M12 14.5h8M12 18h8M12 21.5h5"
        className="stroke-primary-foreground"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function Logo({ href = '/', className }: { href?: string; className?: string }) {
  return (
    <Link
      href={href}
      className={cn('inline-flex items-center gap-2 rounded-md font-semibold tracking-tight', className)}
    >
      <LogoMark />
      <span className="text-base">Vellotalley</span>
    </Link>
  )
}
