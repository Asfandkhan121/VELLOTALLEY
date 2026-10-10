import { ClientHeads } from '@/components/app/client-heads'

export default async function ClientHeadsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <ClientHeads clientId={id} />
}
