type KpiCardProps = {
  label: string
  value: string
  hint?: string
}

export default function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <div className="rounded-2xl border border-cream bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary/50">{label}</p>
      <p className="mt-1 text-2xl font-bold text-primary">{value}</p>
      {hint && <p className="mt-1 text-xs text-primary/60">{hint}</p>}
    </div>
  )
}
