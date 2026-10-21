import ChatWindow from '../components/chat/ChatWindow'
import { useChat } from '../hooks/useChat'

export default function ChatPage() {
  const chat = useChat()

  return (
    <div className="mx-auto flex h-full w-full max-w-[760px] flex-col">
      <ChatWindow chat={chat} />
    </div>
  )
}
