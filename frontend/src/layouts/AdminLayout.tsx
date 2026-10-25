import { Outlet } from 'react-router-dom'
import Logo from '../components/Logo'

export default function AdminLayout() {
  return (
    <div className="min-h-screen bg-white font-sans">
      <header className="border-b border-cream bg-primary">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-4">
          <Logo size={28} />
          <span className="text-lg font-semibold text-white">Celia Admin</span>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
