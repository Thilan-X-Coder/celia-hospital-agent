import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-2xl font-bold text-primary">Page not found</h1>
      <p className="text-primary/70">Sorry, that page doesn't exist.</p>
      <Link
        to="/"
        className="rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white"
      >
        Back to Chat
      </Link>
    </div>
  )
}
