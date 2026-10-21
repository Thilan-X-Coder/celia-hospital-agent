import type { UseChatResult } from '../../hooks/useChat'
import ChatInput from './ChatInput'
import MessageList from './MessageList'
import QuickReplies from './QuickReplies'

type ChatWindowProps = {
  chat: UseChatResult
}

export default function ChatWindow({ chat }: ChatWindowProps) {
  if (chat.phase === 'starting') {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-primary/70">Connecting to Celia...</p>
      </div>
    )
  }

  if (chat.phase === 'start_failed') {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="max-w-sm rounded-2xl border border-accent/30 bg-cream p-6 text-center">
          <p className="font-semibold text-primary">Can't reach the Celia backend</p>
          <p className="mt-1 text-sm text-primary/70">
            Make sure the API server is running, then try again.
          </p>
          <button
            type="button"
            onClick={() => chat.retryStart()}
            className="mt-4 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (chat.phase === 'expired') {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="max-w-sm rounded-2xl border border-accent/30 bg-cream p-6 text-center">
          <p className="font-semibold text-primary">This chat has expired</p>
          <p className="mt-1 text-sm text-primary/70">
            The backend restarted and this conversation is no longer available.
          </p>
          <button
            type="button"
            onClick={() => chat.startNewChat()}
            className="mt-4 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white"
          >
            Start a new chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-cream px-4 py-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary font-bold text-white">
          C
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-primary">Celia - Front Desk Assistant</p>
          <p className="flex items-center gap-1 text-xs text-primary/60">
            <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
            Online
          </p>
        </div>
        {!chat.conversationEnded && (
          <button
            type="button"
            onClick={() => chat.endChat()}
            disabled={chat.isSending}
            className="rounded-full border border-cream px-3 py-1.5 text-xs font-medium text-primary hover:bg-cream/50 disabled:opacity-50"
          >
            End chat
          </button>
        )}
      </div>

      <MessageList
        messages={chat.messages}
        isSending={chat.isSending}
        conversationEnded={chat.conversationEnded}
        onSendMessage={chat.sendMessage}
      />

      {chat.conversationEnded ? (
        <div className="border-t border-cream px-4 py-4 text-center">
          <p className="text-sm font-medium text-primary">Conversation saved. Thank you!</p>
          <button
            type="button"
            onClick={() => chat.startNewChat()}
            className="mt-3 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white"
          >
            Start a new chat
          </button>
        </div>
      ) : (
        chat.showQuickReplies && (
          <QuickReplies onSelect={chat.sendMessage} disabled={chat.isSending} />
        )
      )}

      <ChatInput
        onSend={chat.sendMessage}
        isSending={chat.isSending}
        disabled={chat.conversationEnded}
      />
    </div>
  )
}
