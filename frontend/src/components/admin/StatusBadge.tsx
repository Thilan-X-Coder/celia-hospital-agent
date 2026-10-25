type StatusBadgeProps = {
  status: string
}

const POSITIVE = new Set(['booked', 'Booked'])
const NEGATIVE = new Set(['cancelled', 'Cancelled'])

export default function StatusBadge({ status }: StatusBadgeProps) {
  let className = 'bg-cream text-primary/70'
  if (POSITIVE.has(status)) className = 'bg-success/15 text-success'
  else if (NEGATIVE.has(status)) className = 'bg-accent/15 text-accent'

  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${className}`}>
      {status}
    </span>
  )
}
