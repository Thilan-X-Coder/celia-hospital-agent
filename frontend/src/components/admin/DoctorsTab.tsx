import type { AdminDoctor } from '../../lib/adminApi'
import { formatLkr } from '../../lib/format'
import DataTable from './DataTable'
import type { Column } from './DataTable'

type DoctorsTabProps = {
  doctors: AdminDoctor[]
}

export default function DoctorsTab({ doctors }: DoctorsTabProps) {
  const columns: Column<AdminDoctor>[] = [
    { key: 'doctor', label: 'Doctor', sortable: true },
    { key: 'speciality', label: 'Speciality', sortable: true },
    { key: 'fee', label: 'Fee', sortable: true, render: (row) => formatLkr(row.fee) },
    { key: 'working_days', label: 'Working days' },
    { key: 'free_slots', label: 'Free slots (upcoming)', sortable: true },
    { key: 'booked_slots', label: 'Booked slots (upcoming)', sortable: true },
  ]

  return (
    <DataTable
      columns={columns}
      rows={doctors}
      rowKey={(row) => row.doctor}
      searchKeys={['doctor', 'speciality']}
      searchPlaceholder="Search by doctor or speciality..."
      emptyMessage="No doctors found."
    />
  )
}
