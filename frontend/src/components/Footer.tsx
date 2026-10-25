import { Link } from 'react-router-dom'
import { useHospitalInfo } from '../lib/useHospitalInfo'

export default function Footer() {
  const hospital = useHospitalInfo()
  const hospitalName = hospital.status === 'success' ? hospital.data.name : 'Celia'
  const year = new Date().getFullYear()

  return (
    <footer className="border-t border-cream bg-white py-6 font-sans">
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-1 px-4 text-center text-sm text-primary/70">
        <p className="font-semibold text-primary">{hospitalName}</p>
        <p>Demo project - dummy data only.</p>
        <p>&copy; {year}</p>
        <Link to="/admin" className="text-xs text-primary/40 underline hover:text-primary/70">
          Staff login
        </Link>
      </div>
    </footer>
  )
}
