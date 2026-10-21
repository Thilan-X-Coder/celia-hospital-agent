export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2" aria-label="Celia is typing">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">
        C
      </div>
      <div className="flex items-center gap-1 rounded-2xl border border-cream bg-white px-4 py-3">
        <span className="animate-typing-dot h-2 w-2 rounded-full bg-primary/50" />
        <span className="animate-typing-dot h-2 w-2 rounded-full bg-primary/50 [animation-delay:150ms]" />
        <span className="animate-typing-dot h-2 w-2 rounded-full bg-primary/50 [animation-delay:300ms]" />
      </div>
    </div>
  )
}
