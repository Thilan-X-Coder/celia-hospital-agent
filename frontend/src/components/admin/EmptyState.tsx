type EmptyStateProps = {
  message: string
}

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="rounded-2xl border border-cream bg-cream/40 p-8 text-center text-sm text-primary/60">
      {message}
    </div>
  )
}
