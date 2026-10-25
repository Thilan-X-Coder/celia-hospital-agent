import type { AdminAppointment } from '../../lib/adminApi'
import { getFullInvoiceUrl } from '../../lib/api'
import { formatDate, formatTime12h } from '../../lib/format'
import DataTable from './DataTable'
import type { Column } from './DataTable'
import StatusBadge from './StatusBadge'

type AppointmentsTabProps = {
  appointments: AdminAppointment[]
}

export default function AppointmentsTab({ appointments }: AppointmentsTabProps) {
  const columns: Column<AdminAppointment>[] = [
    { key: 'appointment_id', label: 'ID', sortable: true },
    { key: 'patient_name', label: 'Patient', sortable: true },
    {
      key: 'phone_masked',
      label: 'Phone',
      render: (row) => (
        <span title="Full number is hidden for privacy">{row.phone_masked}</span>
      ),
    },
    { key: 'doctor', label: 'Doctor', sortable: true },
    { key: 'speciality', label: 'Speciality', sortable: true },
    { key: 'date', label: 'Date', sortable: true, render: (row) => formatDate(row.date) },
    { key: 'time', label: 'Time', render: (row) => formatTime12h(row.time) },
    { key: 'status', label: 'Status', sortable: true, render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'invoice_url',
      label: 'Invoice',
      render: (row) =>
        row.invoice_url ? (
          <a
            href={getFullInvoiceUrl(row.invoice_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-accent underline"
          >
            Open invoice
          </a>
        ) : (
          <span className="text-primary/40">-</span>
        ),
    },
  ]

  return (
    <DataTable
      columns={columns}
      rows={appointments}
      rowKey={(row) => row.appointment_id}
      searchKeys={['appointment_id', 'patient_name', 'doctor', 'speciality']}
      searchPlaceholder="Search by patient, doctor, speciality..."
      statusKey="status"
      statusOptions={['booked', 'cancelled']}
      emptyMessage="No appointments yet."
    />
  )
}
