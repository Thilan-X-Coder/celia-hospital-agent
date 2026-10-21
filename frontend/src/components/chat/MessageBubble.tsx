import type { ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import type { ChatMessage } from '../../hooks/useChat'
import BookingConfirmationCard from './BookingConfirmationCard'
import BookingSuccessCard from './BookingSuccessCard'

const markdownComponents = {
  p: ({ children }: { children?: ReactNode }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }: { children?: ReactNode }) => (
    <ul className="mb-2 list-disc pl-5 last:mb-0">{children}</ul>
  ),
  ol: ({ children }: { children?: ReactNode }) => (
    <ol className="mb-2 list-decimal pl-5 last:mb-0">{children}</ol>
  ),
  strong: ({ children }: { children?: ReactNode }) => (
    <strong className="font-semibold">{children}</strong>
  ),
}

function CeliaAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">
      C
    </div>
  )
}

type MessageBubbleProps = {
  message: ChatMessage
  disabled: boolean
  onSendMessage: (text: string) => void
}

export default function MessageBubble({ message, disabled, onSendMessage }: MessageBubbleProps) {
  if (message.kind === 'error') {
    return (
      <div className="animate-message-fade-in flex justify-center">
        <p className="rounded-full bg-emergency/10 px-4 py-1.5 text-xs font-medium text-emergency">
          {message.content}
        </p>
      </div>
    )
  }

  if (message.kind === 'pending_booking') {
    return (
      <div className="animate-message-fade-in flex items-end gap-2 justify-start">
        <CeliaAvatar />
        <BookingConfirmationCard
          pendingBooking={message.pendingBooking}
          disabled={disabled}
          onConfirm={() => onSendMessage('Yes, please confirm the booking')}
          onChange={() => onSendMessage('I would like to change the booking details')}
        />
      </div>
    )
  }

  if (message.kind === 'booking_success') {
    return (
      <div className="animate-message-fade-in flex items-end gap-2 justify-start">
        <CeliaAvatar />
        <BookingSuccessCard booking={message.booking} invoiceUrl={message.invoiceUrl} />
      </div>
    )
  }

  const isAssistant = message.role === 'assistant'

  return (
    <div
      className={`animate-message-fade-in flex items-end gap-2 ${isAssistant ? 'justify-start' : 'justify-end'}`}
    >
      {isAssistant && <CeliaAvatar />}
      <div
        className={
          isAssistant
            ? 'max-w-[80%] rounded-2xl border border-cream bg-white px-4 py-2 text-sm text-primary shadow-sm'
            : 'max-w-[80%] rounded-2xl bg-cream px-4 py-2 text-sm text-primary'
        }
      >
        {isAssistant ? (
          <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkBreaks]}>
            {message.content}
          </ReactMarkdown>
        ) : (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}
      </div>
    </div>
  )
}
