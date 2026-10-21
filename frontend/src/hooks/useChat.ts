import { useEffect, useSyncExternalStore } from 'react'
import {
  ApiError,
  endChat as apiEndChat,
  sendMessage as apiSendMessage,
  startChat,
} from '../lib/api'
import type { BookingOut, PendingBookingOut } from '../lib/api'

export type ChatMessage =
  | { id: string; role: 'user' | 'assistant'; kind: 'text'; content: string }
  | { id: string; kind: 'error'; content: string }
  | { id: string; kind: 'pending_booking'; pendingBooking: PendingBookingOut }
  | { id: string; kind: 'booking_success'; booking: BookingOut; invoiceUrl: string | null }

type Phase = 'starting' | 'ready' | 'expired' | 'start_failed'

interface ChatState {
  phase: Phase
  messages: ChatMessage[]
  sessionId: string | null
  isSending: boolean
  conversationEnded: boolean
}

/**
 * Module-level store (not React state): it must survive ChatPage unmounting/remounting
 * when the patient navigates to About/Contact and back, and it must not re-run on React
 * StrictMode's dev-only double-invoke. A component-level useRef can't do both at once -
 * see the Session 4 plan for why. Lives for the lifetime of the browser tab.
 */
let state: ChatState = {
  phase: 'starting',
  messages: [],
  sessionId: null,
  isSending: false,
  conversationEnded: false,
}

const listeners = new Set<() => void>()

function setState(patch: Partial<ChatState>) {
  state = { ...state, ...patch }
  listeners.forEach((listener) => listener())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot() {
  return state
}

async function begin() {
  setState({ phase: 'starting' })
  try {
    const res = await startChat()
    setState({
      sessionId: res.session_id,
      phase: 'ready',
      messages: [{ id: crypto.randomUUID(), role: 'assistant', kind: 'text', content: res.greeting }],
    })
  } catch {
    setState({ phase: 'start_failed' })
  }
}

let hasStarted = false

function ensureStarted() {
  if (hasStarted) return
  hasStarted = true
  begin()
}

async function doSendMessage(text: string): Promise<boolean> {
  if (!state.sessionId || state.isSending) return false

  const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', kind: 'text', content: text }
  setState({ messages: [...state.messages, userMsg], isSending: true })

  try {
    const res = await apiSendMessage(state.sessionId, text)
    const newMessages: ChatMessage[] = [
      { id: crypto.randomUUID(), role: 'assistant', kind: 'text', content: res.reply },
    ]
    if (res.pending_booking) {
      newMessages.push({
        id: crypto.randomUUID(),
        kind: 'pending_booking',
        pendingBooking: res.pending_booking,
      })
    }
    if (res.booking) {
      newMessages.push({
        id: crypto.randomUUID(),
        kind: 'booking_success',
        booking: res.booking,
        invoiceUrl: res.invoice_url,
      })
    }
    setState({
      messages: [...state.messages, ...newMessages],
      isSending: false,
      conversationEnded: state.conversationEnded || res.conversation_ended,
    })
    return true
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      setState({ phase: 'expired', isSending: false })
    } else {
      setState({
        messages: [
          ...state.messages,
          {
            id: crypto.randomUUID(),
            kind: 'error',
            content: 'Sorry, something went wrong sending that. Please try again.',
          },
        ],
        isSending: false,
      })
    }
    return false
  }
}

async function startNewChat() {
  const oldSessionId = state.sessionId
  if (oldSessionId) {
    try {
      await apiEndChat(oldSessionId)
    } catch {
      // ignore - the old session may already be gone or already saved
    }
  }
  setState({ messages: [], sessionId: null, conversationEnded: false })
  begin()
}

async function doEndChat(): Promise<void> {
  if (!state.sessionId) return
  try {
    await apiEndChat(state.sessionId)
    setState({ conversationEnded: true })
  } catch {
    setState({
      messages: [
        ...state.messages,
        {
          id: crypto.randomUUID(),
          kind: 'error',
          content: 'Sorry, could not end the chat. Please try again.',
        },
      ],
    })
  }
}

export function useChat() {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot)

  useEffect(() => {
    ensureStarted()
  }, [])

  const showQuickReplies =
    snapshot.phase === 'ready' &&
    !snapshot.messages.some((m) => m.kind === 'text' && m.role === 'user')

  return {
    ...snapshot,
    showQuickReplies,
    sendMessage: doSendMessage,
    retryStart: begin,
    startNewChat,
    endChat: doEndChat,
  }
}

export type UseChatResult = ReturnType<typeof useChat>
