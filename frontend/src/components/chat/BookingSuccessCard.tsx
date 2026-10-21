import type { BookingOut } from '../../lib/api'
import { getFullInvoiceUrl } from '../../lib/api'
import { formatDate, formatLkr, formatTime12h } from '../../lib/format'

type BookingSuccessCardProps = {
  booking: BookingOut
  invoiceUrl: string | null
}

export default function BookingSuccessCard({ booking, invoiceUrl }: BookingSuccessCardProps) {
  return (
    <div className="max-w-[80%] rounded-2xl border border-success/30 bg-white p-4 text-sm text-primary shadow-sm">
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-success">
          <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 fill-none stroke-white stroke-[2.5]">
            <path d="M3 8.5L6.2 11.5L13 4.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <p className="font-semibold text-success">Appointment confirmed</p>
      </div>
      <dl className="mt-2 space-y-1 text-primary/80">
        <div className="flex gap-1">
          <dt className="font-medium">Appointment ID:</dt>
          <dd>{booking.appointment_id}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Doctor:</dt>
          <dd>
            {booking.doctor} &middot; {booking.speciality}
          </dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Date:</dt>
          <dd>{formatDate(booking.date)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Time:</dt>
          <dd>{formatTime12h(booking.time)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Fee:</dt>
          <dd>{formatLkr(booking.fee_lkr)}</dd>
        </div>
      </dl>
      {invoiceUrl ? (
        <button
          type="button"
          onClick={() => window.open(getFullInvoiceUrl(invoiceUrl), '_blank', 'noopener,noreferrer')}
          className="mt-4 rounded-full bg-accent px-5 py-2 text-sm font-semibold text-primary"
        >
          Open invoice {booking.invoice_no}
        </button>
      ) : (
        <p className="mt-3 text-primary/70">Your invoice will be given at the front desk.</p>
      )}
    </div>
  )
}
