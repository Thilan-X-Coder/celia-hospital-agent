import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../../hooks/useChat'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'

type MessageListProps = {
  messages: ChatMessage[]
  isSending: boolean
  conversationEnded: boolean
  onSendMessage: (text: string) => void
}

export default function MessageList({
  messages,
  isSending,
  conversationEnded,
  onSendMessage,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    bottomRef.current?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' })
  }, [messages, isSending])

  return (
    <div aria-live="polite" className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
      {messages.map((message, index) => (
        <MessageBubble
          key={message.id}
          message={message}
          disabled={index !== messages.length - 1 || isSending || conversationEnded}
          onSendMessage={onSendMessage}
        />
      ))}
      {isSending && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  )
}
