import { ClientBasis } from '@/components/app/client-basis'

export default async function ClientBasisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <ClientBasis clientId={id} />
}
