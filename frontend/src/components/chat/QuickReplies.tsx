const QUICK_REPLIES = ['Find a doctor', 'Opening hours', 'Book an appointment']

type QuickRepliesProps = {
  onSelect: (text: string) => void
  disabled: boolean
}

export default function QuickReplies({ onSelect, disabled }: QuickRepliesProps) {
  return (
    <div className="flex flex-wrap gap-2 px-4 pb-2">
      {QUICK_REPLIES.map((label) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(label)}
          className="rounded-full border border-accent px-3 py-1.5 text-sm font-medium text-primary hover:bg-accent/10 disabled:opacity-50"
        >
          {label}
        </button>
      ))}
    </div>
  )
}
