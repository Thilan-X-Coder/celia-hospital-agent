import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import Logo from './Logo'
import { useHospitalInfo } from '../lib/useHospitalInfo'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive
    ? 'rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white'
    : 'rounded-full px-4 py-2 text-sm font-semibold text-primary hover:bg-cream'

export default function Navbar() {
  const hospital = useHospitalInfo()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const hospitalName = hospital.status === 'success' ? hospital.data.name : 'Celia'
  const emergencyNumber =
    hospital.status === 'success' ? hospital.data.emergency_number : null

  return (
    <nav aria-label="Main" className="border-b border-cream bg-white font-sans">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-center gap-2">
          <Logo />
          <span className="text-lg font-bold text-primary">{hospitalName}</span>
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <NavLink to="/" end className={navLinkClass}>
            Chat
          </NavLink>
          <NavLink to="/about" className={navLinkClass}>
            About
          </NavLink>
          <NavLink to="/contact" className={navLinkClass}>
            Contact
          </NavLink>
        </div>

        <div className="flex items-center gap-2">
          {emergencyNumber && (
            <a
              href={`tel:${emergencyNumber}`}
              className="rounded-full bg-emergency px-3 py-1 text-xs font-semibold text-white"
            >
              Emergency: {emergencyNumber}
            </a>
          )}

          <button
            type="button"
            aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen((open) => !open)}
            className="rounded-md p-2 text-primary hover:bg-cream md:hidden"
          >
            <svg
              viewBox="0 0 24 24"
              width="22"
              height="22"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              {isMenuOpen ? (
                <path d="M6 6l12 12M18 6L6 18" />
              ) : (
                <path d="M4 7h16M4 12h16M4 17h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {isMenuOpen && (
        <div className="flex flex-col gap-1 border-t border-cream px-4 py-3 md:hidden">
          <NavLink to="/" end className={navLinkClass} onClick={() => setIsMenuOpen(false)}>
            Chat
          </NavLink>
          <NavLink to="/about" className={navLinkClass} onClick={() => setIsMenuOpen(false)}>
            About
          </NavLink>
          <NavLink to="/contact" className={navLinkClass} onClick={() => setIsMenuOpen(false)}>
            Contact
          </NavLink>
        </div>
      )}
    </nav>
  )
}
