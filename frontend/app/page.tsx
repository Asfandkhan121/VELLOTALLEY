import { Hero } from '@/components/landing/hero'
import { Faq, Features, FinalCta, HowItWorks, ProductRoadmap, Security } from '@/components/landing/sections'
import { SiteFooter } from '@/components/landing/site-footer'
import { SiteHeader } from '@/components/landing/site-header'
import { createClient } from '@/lib/supabase/server'

export default async function HomePage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  const signedIn = Boolean(user)

  return (
    <>
      <SiteHeader signedIn={signedIn} />
      <main>
        <Hero signedIn={signedIn} />
        <HowItWorks />
        <ProductRoadmap signedIn={signedIn} />
        <Features />
        <Security />
        <Faq />
        <FinalCta signedIn={signedIn} />
      </main>
      <SiteFooter />
    </>
  )
}
