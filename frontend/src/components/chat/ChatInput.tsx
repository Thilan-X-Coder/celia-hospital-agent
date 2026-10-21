import { useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'

const MAX_LENGTH = 1000
const COUNTER_THRESHOLD = 800

type ChatInputProps = {
  onSend: (text: string) => Promise<boolean>
  isSending: boolean
  disabled?: boolean
}

export default function ChatInput({ onSend, isSending, disabled = false }: ChatInputProps) {
  const [draft, setDraft] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const trimmed = draft.trim()
  const canSend = trimmed.length > 0 && trimmed.length <= MAX_LENGTH && !isSending && !disabled

  async function handleSend() {
    if (!canSend) return
    const ok = await onSend(trimmed)
    if (ok) setDraft('')
    textareaRef.current?.focus()
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-cream px-4 py-3">
      {draft.length > COUNTER_THRESHOLD && (
        <p
          className={`mb-1 text-right text-xs ${draft.length > MAX_LENGTH ? 'text-emergency' : 'text-primary/60'}`}
        >
          {draft.length}/{MAX_LENGTH}
        </p>
      )}
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={MAX_LENGTH}
          rows={1}
          placeholder="Type your message..."
          aria-label="Type your message"
          disabled={disabled}
          className="flex-1 resize-none rounded-2xl border border-cream px-4 py-2 text-sm text-primary outline-none focus:border-primary disabled:opacity-50"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          aria-label="Send message"
          className="rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  )
}
