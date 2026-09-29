import { StatementDetail } from '@/components/app/statement-detail'

export default async function StatementDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <StatementDetail id={id} />
}
