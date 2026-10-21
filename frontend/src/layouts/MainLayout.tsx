import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

export default function MainLayout() {
  const isChatRoute = useLocation().pathname === '/'

  return (
    <div
      className={`flex flex-col bg-white font-sans ${isChatRoute ? 'h-dvh overflow-hidden' : 'min-h-screen'}`}
    >
      <Navbar />
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
      {!isChatRoute && <Footer />}
    </div>
  )
}
