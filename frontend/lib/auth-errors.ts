import type { AuthError } from '@supabase/supabase-js'

export function signInErrorMessage(error: AuthError): string {
  if (error.code === 'email_not_confirmed') {
    return 'Please confirm your email address first — check your inbox for the confirmation link.'
  }
  if (error.status === 429 || error.code === 'over_request_rate_limit') {
    return 'Too many attempts. Please wait a moment and try again.'
  }
  if (error.code === 'invalid_credentials' || error.status === 400) {
    return 'Invalid email or password.'
  }
  return 'Sign in failed unexpectedly. Please try again.'
}

export function signUpErrorMessage(error: AuthError): string {
  if (error.code === 'weak_password') {
    return 'That password is too weak. Use at least 8 characters with a mix of letters and numbers.'
  }
  if (error.status === 429 || error.code?.startsWith('over_')) {
    return 'Too many sign-up attempts. Please wait a few minutes and try again.'
  }
  if (error.code === 'email_address_invalid') {
    return 'Please enter a valid email address.'
  }
  if (error.code === 'user_already_exists') {
    return 'Could not create the account. If you already have one, try logging in.'
  }
  return 'Sign up failed unexpectedly. Please try again.'
}

export function authRedirectUrl(nextPath = '/dashboard') {
  const base =
    process.env.NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL ?? `${window.location.origin}/auth/callback`
  const separator = base.includes('?') ? '&' : '?'
  return `${base}${separator}next=${encodeURIComponent(nextPath)}`
}
