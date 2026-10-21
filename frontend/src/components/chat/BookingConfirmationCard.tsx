import type { PendingBookingOut } from '../../lib/api'
import { formatDate, formatLkr, formatTime12h } from '../../lib/format'

type BookingConfirmationCardProps = {
  pendingBooking: PendingBookingOut
  disabled: boolean
  onConfirm: () => void
  onChange: () => void
}

export default function BookingConfirmationCard({
  pendingBooking,
  disabled,
  onConfirm,
  onChange,
}: BookingConfirmationCardProps) {
  return (
    <div className="max-w-[80%] rounded-2xl border border-cream bg-white p-4 text-sm text-primary shadow-sm">
      <p className="font-semibold">
        {pendingBooking.doctor} &middot; {pendingBooking.speciality}
      </p>
      <dl className="mt-2 space-y-1 text-primary/80">
        <div className="flex gap-1">
          <dt className="font-medium">Date:</dt>
          <dd>{formatDate(pendingBooking.date)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Time:</dt>
          <dd>{formatTime12h(pendingBooking.time)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Fee:</dt>
          <dd>{formatLkr(pendingBooking.fee_lkr)}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Room:</dt>
          <dd>{pendingBooking.room}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="font-medium">Patient:</dt>
          <dd>{pendingBooking.patient_name}</dd>
        </div>
      </dl>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onConfirm}
          disabled={disabled}
          className="rounded-full bg-success px-5 py-2.5 text-lg font-bold text-white disabled:opacity-50"
        >
          Confirm booking
        </button>
        <button
          type="button"
          onClick={onChange}
          disabled={disabled}
          className="rounded-full border border-primary px-5 py-2.5 text-sm font-semibold text-primary disabled:opacity-50"
        >
          Change details
        </button>
      </div>
    </div>
  )
}
