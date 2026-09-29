import { NewConversionForm } from '@/components/app/new-conversion-form'
import { PageHeader } from '@/components/shared/states'
import { getBankProfiles } from '@/lib/bank-profiles'

export default function NewConversionPage() {
  const bankProfiles = getBankProfiles()

  return (
    <>
      <PageHeader
        title="New conversion"
        description="Upload a bank statement PDF and convert it into a reviewed Excel export."
      />
      <NewConversionForm bankProfiles={bankProfiles} />
    </>
  )
}
