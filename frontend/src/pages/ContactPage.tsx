import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useHospitalInfo } from '../lib/useHospitalInfo'

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="border-b border-cream py-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary/50">{label}</p>
      <p className="mt-1 text-primary">{children}</p>
    </div>
  )
}

export default function ContactPage() {
  const hospital = useHospitalInfo()

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-3xl font-bold text-primary">Contact us</h1>

      {hospital.status === 'loading' && (
        <p className="mt-6 text-primary/70">Loading contact details...</p>
      )}

      {hospital.status === 'error' && (
        <div className="mt-6 rounded-2xl border border-accent/30 bg-cream p-6 text-center">
          <p className="font-semibold text-primary">Can't load contact details right now</p>
          <p className="mt-1 text-sm text-primary/70">
            Please make sure the Celia backend is running, then try again.
          </p>
        </div>
      )}

      {hospital.status === 'success' && (
        <div className="mt-6">
          <Row label="Address">{hospital.data.address}</Row>
          <Row label="Phone">
            <a href={`tel:${hospital.data.phone}`} className="underline">
              {hospital.data.phone}
            </a>
          </Row>
          {hospital.data.email && (
            <Row label="Email">
              <a href={`mailto:${hospital.data.email}`} className="underline">
                {hospital.data.email}
              </a>
            </Row>
          )}
          <Row label="Emergency">
            <a href={`tel:${hospital.data.emergency_number}`} className="font-semibold text-emergency">
              {hospital.data.emergency_number}
            </a>
          </Row>
          {hospital.data.opening_hours && <Row label="Opening hours">{hospital.data.opening_hours}</Row>}
          {hospital.data.visiting_hours && (
            <Row label="Visiting hours">{hospital.data.visiting_hours}</Row>
          )}
          {hospital.data.payment_methods && (
            <Row label="Payment methods">{hospital.data.payment_methods}</Row>
          )}
        </div>
      )}

      <div className="mt-10">
        <Link
          to="/"
          className="inline-block rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white"
        >
          Chat with Celia
        </Link>
      </div>
    </div>
  )
}
